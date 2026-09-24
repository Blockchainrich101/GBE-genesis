import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from agent import connect, enqueue, claim, work_once

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'jobs.db'
        self.conn=connect(self.db)
    def tearDown(self):
        self.conn.close(); self.tmp.cleanup()
    def test_idempotency_and_restart(self):
        first=enqueue(self.conn,'Explain a GPU','same')
        self.assertEqual(first,enqueue(self.conn,'Explain a GPU','same'))
        self.conn.close(); self.conn=connect(self.db)
        with patch('agent.infer',return_value='Parallel compute'):
            self.assertEqual(work_once(self.conn,'http://127.0.0.1:8080/v1','local-model'),first[0])
        self.assertEqual(self.conn.execute('SELECT state,result FROM jobs').fetchone(),('succeeded','Parallel compute'))
    def test_recover_expired_lease(self):
        enqueue(self.conn,'task','lease')
        job=claim(self.conn,now=1000)
        self.assertEqual(claim(self.conn,now=1121)[0],job[0])
    def test_retry_is_bounded(self):
        enqueue(self.conn,'task','retry')
        with patch('agent.infer',side_effect=ValueError('model unavailable')):
            for attempt in range(3):
                self.conn.execute("UPDATE jobs SET next_at=0 WHERE idempotency_key='retry'")
                work_once(self.conn,'http://127.0.0.1:8080/v1','local-model')
        self.assertEqual(self.conn.execute('SELECT state,attempts FROM jobs').fetchone(),('failed',3))
    def test_input_rejected(self):
        with self.assertRaises(ValueError): enqueue(self.conn,'','bad')
        with self.assertRaises(ValueError): enqueue(self.conn,'x'*4001,'bad')

if __name__=='__main__': unittest.main()
