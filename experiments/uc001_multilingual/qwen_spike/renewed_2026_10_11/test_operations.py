import http.server, os, socket, socketserver, subprocess, sys, tempfile, threading, time, unittest
from pathlib import Path
from operations import clean_socket, wait_ready, guard_error, stop_owned, owned_rss

class Process:
    def poll(self): return None

class OperationsChecks(unittest.TestCase):
    def test_stale_owned_socket_removed(self):
        with tempfile.TemporaryDirectory(prefix="resolena-harness-", dir="/tmp") as d:
            path=Path(d)/"test.sock"
            sock=socket.socket(socket.AF_UNIX);sock.bind(str(path));sock.close()
            self.assertTrue(clean_socket(path,Path(d)))
            self.assertFalse(path.exists())

    def test_live_socket_preserved(self):
        with tempfile.TemporaryDirectory(prefix="resolena-harness-", dir="/tmp") as d:
            path=Path(d)/"test.sock"
            with socket.socket(socket.AF_UNIX) as sock:
                sock.bind(str(path));sock.listen(1)
                with self.assertRaises(RuntimeError):clean_socket(path,Path(d))
                self.assertTrue(path.exists())

    def test_non_socket_and_foreign_path_preserved(self):
        with tempfile.TemporaryDirectory(prefix="resolena-harness-", dir="/tmp") as d:
            path=Path(d)/"test.sock";path.write_text("keep")
            with self.assertRaises(RuntimeError):clean_socket(path,Path(d))
            self.assertEqual(path.read_text(),"keep")
            with self.assertRaises(RuntimeError):clean_socket(path,Path(d)/"other")

    def test_health_503_waits_until_200(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            calls=0
            def do_GET(self):
                Handler.calls+=1
                self.send_response(503 if Handler.calls==1 else 200)
                self.end_headers();self.wfile.write(b'{"status":"ok"}')
            def log_message(self,*args):pass
        with tempfile.TemporaryDirectory(prefix="resolena-harness-", dir="/tmp") as d:
            path=Path(d)/"health.sock"
            server=socketserver.UnixStreamServer(str(path),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                result=wait_ready(path,Process(),time.time()+2,startup_limit=1,poll=.01)
                self.assertEqual(result["health_attempts"],2)
            finally:server.shutdown();server.server_close();thread.join()

    def test_expired_deadline_and_exited_process_stop(self):
        with self.assertRaises(RuntimeError):wait_ready(Path("/tmp/not-a-model.sock"),Process(),time.time()-1)
        proc=Process();proc.poll=lambda:1
        with self.assertRaises(RuntimeError):wait_ready(Path("/tmp/not-a-model.sock"),proc,time.time()+1)

    def test_post_response_handling_without_model(self):
        import json
        from evaluate_model import call
        class Handler(http.server.BaseHTTPRequestHandler):
            payload=None
            def do_POST(self):
                Handler.payload=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(200);self.end_headers()
                self.wfile.write(json.dumps({"choices":[{"message":{"content":"not JSON"},"finish_reason":"stop"}]}).encode())
            def log_message(self,*args):pass
        with tempfile.TemporaryDirectory(prefix="resolena-harness-",dir="/tmp") as d:
            path=Path(d)/"response.sock";server=socketserver.UnixStreamServer(str(path),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                result=call(str(path),"Synthetic harness request.")
                self.assertIsNone(result["object"])
                self.assertEqual(result["content"],"not JSON")
                self.assertEqual(Handler.payload["messages"][-1]["content"],"Synthetic harness request.")
                self.assertFalse(Handler.payload["chat_template_kwargs"]["enable_thinking"])
            finally:server.shutdown();server.server_close();thread.join()

    def test_guards_and_owned_child_monitoring(self):
        limits={"rss_limit_bytes":100,"available_memory_min_bytes":50}
        self.assertEqual(guard_error(101,60,0,1,limits),"owned_rss_limit")
        self.assertEqual(guard_error(1,49,0,1,limits),"available_ram_limit")
        self.assertEqual(guard_error(1,60,1,1,limits),"deadline")
        self.assertIsNone(guard_error(1,60,0,1,limits))
        proc=subprocess.Popen([sys.executable,"-B","-c","import time;time.sleep(5)"],start_new_session=True)
        try:
            time.sleep(.1)
            self.assertGreater(owned_rss(proc.pid),0)
        finally:stop_owned(proc)
        self.assertIsNotNone(proc.poll())

if __name__=="__main__":unittest.main()
