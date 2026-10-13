import unittest
from ncr import reconstruct
from receipt import make_receipt

EVENTS = [{"agent_id": 1, "delta": -3}, {"agent_id": 2, "delta": 4}]

class EvidenceTests(unittest.TestCase):
    def receipt(self):
        return make_receipt("fixture-001", 1000, EVENTS, reconstruct(1000, EVENTS), "example-source-revision", "3.12")
    def test_repeatable_receipt(self):
        self.assertEqual(self.receipt(), self.receipt())
    def test_unaccepted_status(self):
        self.assertEqual(self.receipt()["status"], "unaccepted_fixture_evidence")
    def test_missing_revision_rejected(self):
        with self.assertRaises(ValueError):
            make_receipt("fixture-001", 1000, EVENTS, reconstruct(1000, EVENTS), "", "3.12")
    def test_result_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            make_receipt("fixture-001", 999, EVENTS, reconstruct(1000, EVENTS), "rev", "3.12")

if __name__ == "__main__":
    unittest.main()
