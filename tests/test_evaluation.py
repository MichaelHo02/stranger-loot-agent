import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from evals.run import grade_asi, grade_discovery, readiness


class EvaluationContractTests(unittest.TestCase):
    def test_outgoing_envelope_log_does_not_pass_asi_gate(self):
        failures = grade_asi({'observer':'cua_visible_ui', 'observed_after_seconds':62,
                              'host_reply_logged_at':'2026-11-07T08:39:59Z',
                              'required_terms':['TrialFinder'], 'evidence_file':'local.png'})
        self.assertIn('No visible agent reply', failures)

    def test_a_late_visible_correct_answer_still_fails_delivery(self):
        failures = grade_asi({'observer':'cua_visible_ui', 'observed_after_seconds':70,
                              'visible_reply_seconds':62, 'visible_reply_text':'TrialFinder',
                              'required_terms':['TrialFinder'], 'evidence_file':'local.png'})
        self.assertIn('Visible reply exceeded 30 seconds', failures)

    def test_fast_help_is_not_a_correct_discovery_answer(self):
        failures = grade_asi({'observer':'cua_visible_ui', 'observed_after_seconds':10,
                              'visible_reply_seconds':2, 'visible_reply_text':'I can help you',
                              'required_terms':['TrialFinder'], 'evidence_file':'local.png'})
        self.assertTrue(any('Missing expected visible' in failure for failure in failures))

    def test_fixture_observation_cannot_claim_live_asi_success(self):
        failures = grade_asi({'observer':'mock', 'observed_after_seconds':10,
                              'visible_reply_seconds':2, 'visible_reply_text':'TrialFinder',
                              'required_terms':['TrialFinder'], 'evidence_file':'local.png'})
        self.assertTrue(any('Missing visible UI observation' in failure for failure in failures))

    def test_expected_candidate_and_latency_are_required(self):
        failures = grade_discovery({'expected_name':'TrialFinder'}, [], 31)
        self.assertEqual(len(failures), 2)

    def test_unrelated_candidate_is_not_a_no_match_success(self):
        failures = grade_discovery({'expect_empty':True}, [{'name':'Random Agent'}], 1)
        self.assertTrue(failures)

    def test_correct_visible_fast_reply_can_pass(self):
        self.assertEqual(grade_asi({'observer':'cua_visible_ui', 'observed_after_seconds':10,
                                    'visible_reply_seconds':2, 'visible_reply_text':'1. TrialFinder',
                                    'required_terms':['TrialFinder'], 'evidence_file':'local.png'}), [])

    def test_readiness_fails_when_reports_are_missing(self):
        with TemporaryDirectory() as directory, patch('evals.run.subprocess.check_output', return_value='abc\n'):
            results = readiness(Path(directory))
        self.assertTrue(all(result['status'] == 'fail' for result in results))

    def test_readiness_regrades_asi_instead_of_trusting_claimed_pass(self):
        with TemporaryDirectory() as directory, patch('evals.run.subprocess.check_output', return_value='abc\n'):
            root = Path(directory)
            for layer in ('fixture', 'mcp', 'asi'):
                report = {'layer':layer, 'commit':'abc', 'gate':'pass', 'results':[{'id':'case','status':'pass'}]}
                (root / (layer + '.json')).write_text(json.dumps(report))
            results = readiness(root)
        self.assertEqual(results[0]['status'], 'pass')
        self.assertEqual(results[1]['status'], 'pass')
        self.assertEqual(results[2]['status'], 'fail')
        self.assertIn('No visible agent reply', results[2]['failures'])
