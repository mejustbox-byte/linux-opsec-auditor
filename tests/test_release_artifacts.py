"""Publication guard tests use a disposable synthetic Git repository, never a live release."""
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from release_artifacts import checksums, verify, verify_release_metadata, VerificationError, COMMIT, TAG, RELEASE_ID, WHEEL, SOURCE, ASSETS


class ReleaseGuardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='opsec-release-guard-')
        self.root = Path(self.temp.name)
        self.repo = self.root/'repo'; self.repo.mkdir()
        self.assets = self.root/'assets'; self.assets.mkdir()
        self.files = {'src/linux_opsec_auditor/__init__.py': b'__version__ = "0.1.0a1"\n',
                      'README.md': b'Synthetic release guard fixture\n', '.gitignore': b'build/\n'}
        for name, content in self.files.items():
            path = self.repo/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(content)
        self.git('init','--initial-branch=main')
        self.git('add','.')
        self.git('-c','user.name=Synthetic Test','-c','user.email=synthetic@example.invalid','commit','-m','Synthetic fixture')
        self.commit = self.git('rev-parse','HEAD').decode().strip()
        self.git('tag',TAG)
        self.make_wheel()
        self.make_source()
        checksums(self.assets)

    def tearDown(self):
        self.temp.cleanup()

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL)

    def make_wheel(self, extra=None, changed=False):
        with zipfile.ZipFile(self.assets/WHEEL,'w') as wheel:
            wheel.writestr('linux_opsec_auditor/__init__.py',b'wrong source' if changed else self.files['src/linux_opsec_auditor/__init__.py'])
            wheel.writestr('linux_opsec_auditor-0.1.0a1.dist-info/METADATA',
                           'Metadata-Version: 2.4\nVersion: 0.1.0a1\nRequires-Python: >=3.12\n')
            if extra:
                wheel.writestr(extra,b'unexpected fixture')

    def make_source(self, changed=False, extra=None):
        with tarfile.open(self.assets/SOURCE,'w:gz') as archive:
            for name,content in self.files.items():
                if name == '.gitignore': continue
                if changed and name == 'README.md': content=b'wrong source'
                info=tarfile.TarInfo('linux_opsec_auditor-0.1.0a1/'+name); info.size=len(content)
                archive.addfile(info,BytesIO(content))
            if extra:
                info=tarfile.TarInfo(extra); info.size=1
                archive.addfile(info,BytesIO(b'x'))

    def verify(self):
        return verify(self.assets,self.repo,self.commit,TAG)

    def test_valid_source_wheel_and_checksums(self):
        result=self.verify()
        self.assertEqual(set(result),{WHEEL,SOURCE})

    def test_tag_must_match_expected_commit(self):
        with self.assertRaises(VerificationError): verify(self.assets,self.repo,'0'*40,TAG)

    def test_malformed_duplicate_unexpected_checksum_entries(self):
        for bad in ['invalid\n',f'{"a"*64}  ../../escape\n',
                    f'{"a"*64}  {WHEEL}\n'*2,f'{"a"*64}  unknown.whl\n']:
            with self.subTest(bad=bad[:12]):
                (self.assets/'SHA256SUMS').write_text(bad)
                with self.assertRaises(VerificationError): self.verify()

    def test_tampered_file_fails_integrity(self):
        (self.assets/WHEEL).write_bytes(b'corrupt synthetic wheel')
        with self.assertRaises(VerificationError): self.verify()

    def test_hash_valid_but_wrong_wheel_source_rejected(self):
        self.make_wheel(changed=True); checksums(self.assets)
        with self.assertRaises(VerificationError): self.verify()

    def test_unexpected_wheel_payload_rejected(self):
        self.make_wheel(extra='unexpected_module.py'); checksums(self.assets)
        with self.assertRaises(VerificationError): self.verify()

    def test_hash_valid_but_wrong_source_rejected(self):
        self.make_source(changed=True); checksums(self.assets)
        with self.assertRaises(VerificationError): self.verify()

    def test_archive_traversal_rejected(self):
        self.make_source(extra='../../escape'); checksums(self.assets)
        with self.assertRaises(VerificationError): self.verify()

    def metadata(self):
        return {'id':RELEASE_ID,'tag_name':TAG,'target_commitish':COMMIT,
                'draft':False,'prerelease':True,
                'assets':[{'name':name,'state':'uploaded','size':123} for name in sorted(ASSETS)]}

    def test_existing_release_identity_and_complete_public_assets(self):
        verify_release_metadata(self.metadata(),public=True,require_assets=True)
        for key,value in [('id',1),('tag_name','other'),('target_commitish','0'*40),('prerelease',False),('draft',True)]:
            data=self.metadata(); data[key]=value
            with self.subTest(key=key):
                with self.assertRaises(VerificationError): verify_release_metadata(data,public=True,require_assets=True)

    def test_partial_unexpected_and_unready_assets_rejected(self):
        for kind in ['partial','extra','empty','pending','duplicate']:
            data=self.metadata()
            if kind=='partial':data['assets'].pop()
            if kind=='extra':data['assets'].append({'name':'unexpected','state':'uploaded','size':1})
            if kind=='empty':data['assets'][0]['size']=0
            if kind=='pending':data['assets'][0]['state']='new'
            if kind=='duplicate':data['assets'].append(data['assets'][0].copy())
            with self.subTest(kind=kind):
                with self.assertRaises(VerificationError): verify_release_metadata(data,require_assets=True)
