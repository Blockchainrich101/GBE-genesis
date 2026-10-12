import unittest
from ncr import reconstruct

class NCRTests(unittest.TestCase):
    def test_deterministic(self):
        events = [{"agent_id": 1, "delta": -3}, {"agent_id": 2, "delta": 4}]
        self.assertEqual(reconstruct(1000, events), reconstruct(1000, events))
    def test_resources(self):
        self.assertEqual(reconstruct(3, [{"agent_id": 0, "delta": -20}])["total_resources"], 20)
    def test_reject_unknown_agent(self):
        with self.assertRaises(ValueError):
            reconstruct(2, [{"agent_id": 3, "delta": 1}])
    def test_reject_noninteger_delta(self):
        with self.assertRaises(ValueError):
            reconstruct(2, [{"agent_id": 0, "delta": True}])

if __name__ == "__main__":
    unittest.main()
