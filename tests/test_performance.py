import unittest
from unittest.mock import patch
from evals.performance import evaluate, percentile


class PerformanceGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_realistic_scenarios_pass_handler_and_saved_state_flow(self):
        results = await evaluate(1, 250)
        self.assertEqual(len(results), 6)
        self.assertTrue(all(result['status'] == 'pass' for result in results), results)
        self.assertTrue(all(result['turns_measured'] == 3 for result in results))

    async def test_latency_regression_fails_gate(self):
        async def slow(*args):
            return [300], []
        with patch('evals.performance.sample', side_effect=slow):
            results = await evaluate(1, 250)
        self.assertTrue(all(result['status'] == 'fail' for result in results))

    def test_tail_percentile_is_nearest_rank(self):
        self.assertEqual(percentile(list(range(1, 21)), .95), 19)
        self.assertIsNone(percentile([], .95))
