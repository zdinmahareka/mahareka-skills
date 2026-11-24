"""chief-of-staff: ask_master.py sends a question to the machine that holds a skill and prints the answer."""
import http.server, json, os, shutil, subprocess, sys, tempfile, threading, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
TOOL = Path(__file__).resolve().parents[1] / "skills" / "chief-of-staff" / "_tools" / "ask_master.py"
KEY = "k" * 40

class FakeMissionControl(http.server.BaseHTTPRequestHandler):
    """Answers like Mission Control's /api/bridge/ask. The second GET returns the answer."""
    seen, polls, mode = [], 0, "answer"
    def log_message(self, *a): pass
    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8"); self.send_response(code); self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        cls = type(self); n = int(self.headers.get("content-length") or 0); body = json.loads(self.rfile.read(n) or b"{}")
        cls.seen.append((self.path, self.headers.get("authorization"), body))
        if self.headers.get("authorization") != f"Bearer {KEY}": return self._send(401, {"error": "unknown bridge token"})
        if cls.mode == "local": return self._send(409, {"error": "Aira's work runs on your own machine: do it here.", "code": "local"})
        if cls.mode == "limit": return self._send(429, {"error": "3 questions are still waiting for an answer."})
        self._send(201, {"id": "11111111-2222-3333-4444-555555555555", "staff": "Hakim", "answeredBy": "MatDuo"})
    def do_GET(self):
        cls = type(self); cls.polls += 1
        if cls.mode == "never" or cls.polls < 2: return self._send(200, {"status": "waiting", "answeredBy": "MatDuo"})
        self._send(200, {"status": "answered", "answeredBy": "MatDuo", "answer": "Hakim (QS): RM 4.50/sqft, siap cat."})

class AskMaster(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        FakeMissionControl.seen, FakeMissionControl.polls, FakeMissionControl.mode = [], 0, "answer"
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeMissionControl)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close); self.addCleanup(self.srv.shutdown)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("MAHAREKA_") and k.lower() not in ("http_proxy", "https_proxy", "all_proxy")}
        self.env.update(HOME=self.home.as_posix(), USERPROFILE=str(self.home), NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")

    def link(self, url=None, name="mattigo.env", extra="MC_RUN_TASKS=true\n"):
        d = self.home / "mahareka-mission-control" / "deploy"; d.mkdir(parents=True, exist_ok=True)
        url = url or f"http://127.0.0.1:{self.srv.server_address[1]}/api/ingest"
        (d / name).write_text(f"MC_AGENT_ID={name[:-4]}\nMC_INGEST_URL={url}\nMC_BRIDGE_TOKEN={KEY}\n{extra}", encoding="utf-8")

    def run_tool(self, *args, stdin=None):
        return subprocess.run([sys.executable, "-P", str(TOOL), *args], capture_output=True, text=True, encoding="utf-8", env=self.env, input=stdin, timeout=60)

    def test_no_link_says_so_and_asks_nothing(self):
        p = self.run_tool("ask", "Berapa rate plaster ceiling?")
        self.assertEqual(p.returncode, 2); self.assertIn("NO LINK", p.stdout); self.assertEqual(FakeMissionControl.seen, [])

    def test_asks_waits_and_prints_the_answer_without_the_key(self):
        self.link()
        p = self.run_tool("ask", "--desk", "qs", "--wait", "30", "Berapa rate plaster ceiling per sqft, siap cat?")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ASKED id=11111111-2222-3333-4444-555555555555 · Hakim on MatDuo", p.stdout)
        self.assertIn("ANSWER from MatDuo:\nHakim (QS): RM 4.50/sqft, siap cat.", p.stdout)
        path, auth, body = FakeMissionControl.seen[0]
        self.assertEqual((path, auth, body), ("/api/bridge/ask", f"Bearer {KEY}", {"desk": "qs", "question": "Berapa rate plaster ceiling per sqft, siap cat?"}))
        self.assertNotIn(KEY, p.stdout + p.stderr, "the key is never printed")

    def test_not_ready_then_get(self):
        self.link(); FakeMissionControl.mode = "never"
        p = self.run_tool("ask", "--wait", "0", "-", stdin="Soalan panjang\ndari stdin")
        self.assertEqual(p.returncode, 0); self.assertIn("WAITING id=11111111-2222-3333-4444-555555555555", p.stdout)
        self.assertEqual(FakeMissionControl.seen[0][2]["question"], "Soalan panjang\ndari stdin")
        FakeMissionControl.mode, FakeMissionControl.polls = "answer", 5
        g = self.run_tool("get", "11111111-2222-3333-4444-555555555555", "--wait", "5")
        self.assertIn("ANSWER from MatDuo", g.stdout); self.assertIn("not a question id", self.run_tool("get", "../../etc").stdout)

    def test_local_limit_and_the_right_link(self):
        # the files-only design agent's link is never chosen over the agent that runs tasks
        self.link(url="http://127.0.0.1:9/api/ingest", name="a-design.env", extra="HERMES_USE_CLI=false\n"); self.link()
        FakeMissionControl.mode = "local"
        p = self.run_tool("ask", "--desk", "lead", "Tulis caption raya")
        self.assertEqual(p.returncode, 3); self.assertIn("LOCAL: Aira's work runs on your own machine", p.stdout)
        FakeMissionControl.mode = "limit"
        self.assertIn("LIMIT: 3 questions", self.run_tool("ask", "Lagi satu soalan").stdout)

    def test_the_key_only_travels_over_https(self):
        self.link(url="http://mc.example.ts.net/api/ingest")            # plain http to a real host: refused
        p = self.run_tool("ask", "Berapa rate?")
        self.assertEqual(p.returncode, 2); self.assertIn("NO LINK", p.stdout)

if __name__ == "__main__":
    unittest.main()
