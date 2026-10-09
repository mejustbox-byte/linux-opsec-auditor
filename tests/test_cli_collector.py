"""Actual CLI and filesystem integration on synthetic roots; not host validation."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from linux_opsec_auditor.collector import SafeRoot, collect, parse_ssh, parse_os_release, read_input
from linux_opsec_auditor.cli import main, write_private
from linux_opsec_auditor.schema import InputError, loads
from test_auditor import fixture


class FilesystemTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='opsec-synthetic-')
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def file(self,path,content,mode=0o600):
        target=self.root/path; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content); target.chmod(mode); return target

    def test_read_regular_size_symlink_directory_fifo_and_device(self):
        regular=self.file('regular','hello')
        safe=SafeRoot(self.root)
        try:
            self.assertEqual(safe.read('regular',5),b'hello')
            with self.assertRaises(InputError): safe.read('regular',4)
            (self.root/'link').symlink_to(regular)
            with self.assertRaises(InputError): safe.read('link')
            (self.root/'dir').mkdir()
            with self.assertRaises(InputError): safe.read('dir')
            os.mkfifo(self.root/'fifo')
            with self.assertRaises(InputError): safe.read('fifo')
            for path in ['../regular','/regular','./regular','regular/../regular']:
                with self.assertRaises(InputError): safe.read(path)
            (self.root/'parent-link').symlink_to(self.root,target_is_directory=True)
            with self.assertRaises(OSError): safe.read('parent-link/regular')
        finally:
            safe.close()
        # O_PATH validates devices without opening them for reading.
        with self.assertRaises(InputError): read_input('/dev/null')

    def test_root_parent_symlink_rejected(self):
        self.file('real/input', 'synthetic')
        (self.root/'alias').symlink_to(self.root/'real', target_is_directory=True)
        (self.root/'real/nested').mkdir()
        with self.assertRaises(OSError):
            SafeRoot(self.root/'alias/nested')

    def test_failed_output_is_removed_without_overwriting(self):
        target = self.root/'report'
        with patch('linux_opsec_auditor.cli.os.fsync', side_effect=OSError('synthetic failure')):
            with self.assertRaises(OSError):
                write_private(target, 'synthetic-only')
        self.assertFalse(target.exists())
        write_private(target, 'successful retry')
        self.assertEqual(target.read_text(), 'successful retry')

    def test_output_private_create_only_and_reject_symlinks(self):
        output=self.root/'report.json'
        write_private(output,'private-fixture')
        self.assertEqual(stat.S_IMODE(output.stat().st_mode),0o600)
        with self.assertRaises(FileExistsError): write_private(output,'replacement')
        self.assertEqual(output.read_text(),'private-fixture')
        (self.root/'link').symlink_to(output)
        with self.assertRaises(OSError): write_private(self.root/'link','replacement')
        self.root.chmod(0o755)
        with self.assertRaises(InputError): write_private(self.root/'new','private-fixture')

    def test_local_collection_missing_and_no_writes(self):
        self.file('etc/os-release','ID=ubuntu\nVERSION_ID="24.04"\n')
        self.file('etc/ssh/sshd_config','PermitRootLogin yes\nPasswordAuthentication no\n')
        self.file('etc/passwd','synthetic-only\n',0o666)
        self.file('etc/group','synthetic-only\n')
        # No sudoers. Permission metadata can still detect a known writable file.
        before={str(p.relative_to(self.root)):(p.read_bytes(),p.stat().st_mode) for p in self.root.rglob('*') if p.is_file()}
        snap=collect(str(self.root))
        loads(json.dumps(snap).encode())
        self.assertEqual(snap['platform']['family'],'ubuntu')
        self.assertTrue(snap['observations']['ssh']['values']['permit_root'])
        self.assertFalse(snap['observations']['ssh']['values']['effective'])
        self.assertTrue(snap['observations']['files']['values']['group_world_writable'])
        self.assertFalse(snap['observations']['lsm']['values']['host_context'])
        after={str(p.relative_to(self.root)):(p.read_bytes(),p.stat().st_mode) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_collector_symlinks_and_invalid_utf8_unavailable(self):
        self.file('usr/lib/os-release','ID=debian\nVERSION_ID="13"\n')
        (self.root/'etc').mkdir()
        (self.root/'etc/os-release').symlink_to(self.root/'usr/lib/os-release')
        path=self.file('etc/ssh/sshd_config','')
        path.write_bytes(b'\xff')
        snap=collect(str(self.root))
        self.assertEqual(snap['platform']['version'],'13')
        self.assertEqual(snap['observations']['ssh']['state'],'unavailable')

    def test_parser_scope_and_vendor_separation(self):
        self.assertEqual(parse_os_release('ID=rhel\nVERSION_ID="9.7"\n'),('rhel','9'))
        self.assertEqual(parse_os_release('ID=almalinux\nVERSION_ID="9.7"\n'),('other','9.7'))
        self.assertEqual(parse_ssh('Include conf.d/*.conf\nPermitRootLogin yes\n'),{'effective':False})
        self.assertEqual(parse_ssh('Include\tconf.d/*.conf\nPermitRootLogin yes\n'),{'effective':False})
        self.assertNotIn('permit_root',parse_ssh('Match User synthetic\nPermitRootLogin yes\n'))
        self.assertFalse(parse_ssh('PermitRootLogin no\nPermitRootLogin yes\n')['permit_root'])
        self.assertNotIn('permit_root',parse_ssh('PermitRootLogin invalid\nPermitRootLogin no\n'))

    def run_main(self,args):
        out=io.StringIO(); err=io.StringIO()
        with redirect_stdout(out),redirect_stderr(err): result=main(args)
        return result,out.getvalue(),err.getvalue()

    def snapshot_file(self,name='healthy'):
        snap=fixture(name); snap['collected_at']=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        return self.file('input.json',json.dumps(snap))

    def test_cli_exit_semantics_and_formats(self):
        path=self.snapshot_file()
        result,out,err=self.run_main(['audit','--input',str(path),'--format','json'])
        self.assertEqual(result,0); self.assertEqual(err,'')
        self.assertEqual(json.loads(out)['summary']['pass'],12)
        path=self.snapshot_file('unsafe')
        result,out,_=self.run_main(['audit','--input',str(path)])
        self.assertEqual(result,1); self.assertIn('[FAIL] SSH-01',out)
        result,_,_=self.run_main(['audit','--input',str(path),'--fail-on','none'])
        self.assertEqual(result,0)
        path=self.snapshot_file('unavailable')
        result,_,_=self.run_main(['audit','--input',str(path),'--fail-on','incomplete'])
        self.assertEqual(result,3)
        result,_,_=self.run_main(['audit','--input',str(path)])
        self.assertEqual(result,0) # Exit 0 alone is NOT proof of complete evidence.

    def test_cli_collect_then_audit_private_output(self):
        self.file('etc/os-release','ID=ubuntu\nVERSION_ID="24.04"\n')
        snap=self.root/'snapshot.json'; report=self.root/'report.json'
        result,_,_=self.run_main(['collect','--root',str(self.root),'--output',str(snap)])
        self.assertEqual(result,0)
        result,_,_=self.run_main(['audit','--input',str(snap),'--output',str(report),'--format','json','--fail-on','incomplete'])
        self.assertEqual(result,3)
        self.assertEqual(json.loads(report.read_text())['summary']['unknown'],12)
        self.assertEqual(stat.S_IMODE(report.stat().st_mode),0o600)
        result,_,err=self.run_main(['collect','--root',str(self.root),'--output',str(snap)])
        self.assertEqual(result,2); self.assertNotIn(str(snap),err)

    def test_cli_invalid_payload_does_not_print_secrets_or_path(self):
        path=self.file('private-fixture-path','{"secret-private-fixture":"private-fixture-content"}')
        result,out,err=self.run_main(['audit','--input',str(path)])
        self.assertEqual(result,2); self.assertEqual(out,'')
        self.assertNotIn('private-fixture',err)
        path.unlink()
        result,_,err=self.run_main(['audit','--input',str(path)])
        self.assertEqual(result,2); self.assertNotIn('private-fixture',err)

    def test_real_subprocess_cli_and_schema(self):
        result=subprocess.run([sys.executable,'-m','linux_opsec_auditor','schema'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['properties']['schema_version']['const'],1)
        invalid=subprocess.run([sys.executable,'-m','linux_opsec_auditor','audit'],capture_output=True,text=True,timeout=10)
        self.assertEqual(invalid.returncode,2)


if __name__ == '__main__':
    unittest.main()
