"""Synthetic rule and attack-input tests; no real infrastructure evidence."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from linux_opsec_auditor.rules import audit, render_text, RULES
from linux_opsec_auditor.schema import loads, InputError, MAX_BYTES, INPUT_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)


def fixture(name='healthy'):
    return loads((ROOT / 'fixtures' / f'{name}.json').read_bytes())


class RulesTest(unittest.TestCase):
    def test_fixture_outcomes_all_twelve_checks(self):
        for name, expected in [('healthy','pass'), ('unsafe','fail'), ('unavailable','unknown'), ('not-run','not_run')]:
            with self.subTest(name=name):
                report = audit(fixture(name), now=NOW)
                self.assertEqual(len(report['findings']), 12)
                self.assertEqual(report['summary'][expected], 12)
                for finding in report['findings']:
                    self.assertTrue(finding['remediation'])
                    self.assertTrue(finding['limitation'])
                    self.assertTrue(finding['reason'])
                    self.assertEqual(finding['confidence'], 'asserted')

    def test_each_group_empty_unknown(self):
        snap = fixture()
        for group in RULES:
            with self.subTest(group=group):
                candidate = copy.deepcopy(snap)
                candidate['observations'][group]['values'] = {}
                report = audit(candidate, now=NOW, selected=[group])
                self.assertEqual(report['summary'], {'pass':0,'fail':0,'unknown':1,'not_run':11})

    def test_each_required_fact_missing_cannot_pass(self):
        snap = fixture()
        for group, obs in snap['observations'].items():
            for key in obs['values']:
                with self.subTest(group=group,key=key):
                    candidate = copy.deepcopy(snap)
                    del candidate['observations'][group]['values'][key]
                    result = audit(candidate, selected=[group], now=NOW)
                    finding = next(f for f in result['findings'] if f['check_id'] == RULES[group][0])
                    # LSM may pass with either enforcing mechanism; unused SELinux peer is optional.
                    if group == 'lsm' and key == 'apparmor_enforcing':
                        self.assertEqual(finding['status'], 'pass')
                    else:
                        self.assertEqual(finding['status'], 'unknown')

    def test_stale_future_and_date_boundaries(self):
        snap = fixture()
        for date in [NOW + timedelta(days=2), NOW - timedelta(hours=25)]:
            snap['collected_at'] = date.strftime('%Y-%m-%dT%H:%M:%SZ')
            self.assertEqual(audit(snap, now=NOW)['summary']['unknown'], 12)
        snap['collected_at'] = (NOW-timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.assertEqual(audit(snap, now=NOW)['summary']['pass'], 12)

    def test_candidate_profiles_separate_from_validation(self):
        snap = fixture()
        for family, versions in {'ubuntu':['22.04','24.04'],'debian':['12','13'],'rhel':['9','10']}.items():
            for version in versions:
                snap['platform'].update(family=family, version=version)
                report = audit(snap, now=NOW)
                self.assertEqual(report['summary']['pass'],12)
                self.assertEqual(report['platform_validation'],'unverified_candidate')
        for family, version, arch in [('ubuntu','26.04','x86_64'),('other','9','x86_64'),('rhel','9','aarch64')]:
            snap['platform'].update(family=family, version=version, architecture=arch)
            self.assertEqual(audit(snap, now=NOW)['summary']['unknown'],12)

    def test_static_runtime_evidence_and_namespace(self):
        snap = fixture()
        for group in ['ssh','lsm','systemd','logs','kernel','containers']:
            snap['observations'][group]['source'] = 'static'
        self.assertEqual(audit(snap, now=NOW)['summary']['unknown'],6)
        snap = fixture()
        snap['observations']['lsm']['values']['host_context'] = False
        self.assertEqual(audit(snap, selected=['lsm'], now=NOW)['summary']['unknown'],1)

    def test_known_unsafe_static_ssh_is_not_silenced(self):
        snap = fixture('unsafe')
        snap['observations']['ssh']['values']['effective'] = False
        snap['observations']['ssh']['source'] = 'static'
        self.assertEqual(audit(snap, selected=['ssh'], now=NOW)['summary']['fail'],1)

    def test_skipped_evidence_not_leaked(self):
        report = audit(fixture(), selected=[], now=NOW)
        self.assertEqual(report['summary']['not_run'],12)
        self.assertTrue(all(f['evidence'] == {} for f in report['findings']))

    def test_digest_redaction_and_determinism(self):
        snap = fixture()
        report = audit(snap, now=NOW)
        self.assertEqual(report,audit(snap,now=NOW))
        self.assertNotIn('a'*64,json.dumps(report))
        self.assertNotIn('a'*64,render_text(report))
        self.assertIn('digests_equal',render_text(report))
        self.assertEqual(snap,fixture())

    def test_bad_selection_rejected(self):
        with self.assertRaises(ValueError):
            audit(fixture(), selected=['untrusted-command'],now=NOW)


class SchemaTest(unittest.TestCase):
    def assert_invalid(self, value):
        with self.assertRaises(InputError):
            loads(json.dumps(value).encode())

    def test_export_matches_runtime(self):
        for path in [ROOT/'schemas/input-v1.schema.json',ROOT/'src/linux_opsec_auditor/input-v1.schema.json']:
            self.assertEqual(json.loads(path.read_text()),INPUT_SCHEMA)

    def test_unknown_fields_and_secret_not_echoed(self):
        for location in ['root','platform','observation','values']:
            value = fixture()
            targets={'root':value,'platform':value['platform'],
                     'observation':value['observations']['ssh'],
                     'values':value['observations']['ssh']['values']}
            targets[location]['secret-private-fixture-marker'] = 'private-fixture-marker'
            with self.assertRaises(InputError) as caught:
                loads(json.dumps(value).encode())
            self.assertNotIn('private-fixture-marker',str(caught.exception))

    def test_schema_strict_types_ranges_and_dates(self):
        for bad in [True,'1',2,None]:
            value=fixture(); value['schema_version']=bad; self.assert_invalid(value)
        for bad in [1,'false',None,[],{}]:
            value=fixture(); value['observations']['ssh']['values']['permit_root']=bad; self.assert_invalid(value)
        for bad in [-1,1_000_001,True,1.1,'12']:
            value=fixture(); value['observations']['backups']['values']['age_hours']=bad; self.assert_invalid(value)
        for bad in ['2026-02-30T00:00:00Z','2026-10-09','2026-10-09T00:00:00+00:00','private-fixture-marker']:
            value=fixture(); value['collected_at']=bad; self.assert_invalid(value)
        value=fixture(); value['observations']['drift']['values']['baseline_sha256']='bad'; self.assert_invalid(value)

    def test_unavailable_cannot_contain_values(self):
        for state in ['unavailable','not_run']:
            value=fixture(); value['observations']['ssh']['state']=state; self.assert_invalid(value)

    def test_missing_fields(self):
        for key in INPUT_SCHEMA['required']:
            value=fixture(); del value[key]; self.assert_invalid(value)

    def test_hostile_json(self):
        payloads=[b'{',b'\xff',b'{"schema_version":1,"schema_version":1}',b'NaN',b'Infinity',
                  b'['*2000+b']'*2000,b' '* (MAX_BYTES+1),b'1'*5000]
        for payload in payloads:
            with self.subTest(size=len(payload)):
                with self.assertRaises(InputError): loads(payload)


if __name__ == '__main__':
    unittest.main()
