import tempfile
import unittest
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from agent import connect, enqueue, claim, work_once, health, run, infer

class ModelHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length=int(self.headers['Content-Length'])
        body=json.loads(self.rfile.read(length))
        if self.path != '/v1/chat/completions' or body['model'] != 'test-model':
            self.send_error(400); return
        output=json.dumps({'choices':[{'message':{'content':'local response'}}]}).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(output)))
        self.end_headers()
        self.wfile.write(output)
    def log_message(self, *args):
        pass

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
    def test_continuous_worker_records_health_and_stops(self):
        enqueue(self.conn,'task','continuous')
        with patch('agent.infer',return_value='answer'):
            self.assertEqual(run(self.conn,'http://127.0.0.1:8080/v1','local-model',poll=0.1,max_jobs=1),1)
        self.assertEqual(health(self.conn)['worker'],'stopped')
        self.assertEqual(health(self.conn)['jobs']['succeeded'],1)
        self.conn.close(); self.conn=connect(self.db)
        self.assertEqual(health(self.conn)['processed'],1)
    def test_stale_heartbeat_is_reported(self):
        from agent import heartbeat
        with patch('agent.time.time',return_value=100):
            heartbeat(self.conn,'running',0)
        self.assertEqual(health(self.conn,now=116)['worker'],'stale')
    def test_actual_loopback_protocol(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),ModelHandler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            endpoint=f'http://127.0.0.1:{server.server_port}/v1'
            enqueue(self.conn,'a sample task','http')
            work_once(self.conn,endpoint,'test-model')
            self.assertEqual(self.conn.execute('SELECT state,result FROM jobs').fetchone(),('succeeded','local response'))
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)

if __name__=='__main__': unittest.main()
