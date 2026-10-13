import hashlib
import json
import unittest
from ncr import reconstruct

FIXTURE = ({'agent_id': 1, 'delta': -3}, {'agent_id': 2, 'delta': 4})
EXPECTED_STATE_SHA256 = '394e204c01006dd832613a1c5a95e50ee2ef6f96d27d847137fdad61746a4057'

class ReceiptContractTests(unittest.TestCase):
    def test_known_fixture_state(self):
        result = reconstruct(1000, FIXTURE)
        self.assertEqual(result['state_sha256'], EXPECTED_STATE_SHA256)
        self.assertEqual(result['total_resources'], 10001)

    def test_fixture_fingerprint_format(self):
        payload = json.dumps(FIXTURE, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(len(hashlib.sha256(payload).hexdigest()), 64)

    def test_repeat_reconstruction(self):
        self.assertEqual(reconstruct(1000, FIXTURE), reconstruct(1000, FIXTURE))

if __name__ == '__main__':
    unittest.main()
