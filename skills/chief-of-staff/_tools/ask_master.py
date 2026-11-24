#!/usr/bin/env python3
"""
Ask a staff member whose work runs on another machine, through Mission Control, and print the
answer. Example: the laptop holds no ratebase, so a rate or costing question goes to Hakim on
MatDuo:

    python ask_master.py ask --desk qs "Berapa rate plaster ceiling per sqft, siap cat?"
    python ask_master.py get <id>            # fetch an answer that was not ready yet

The question becomes an Answer-only task for that staff member. It is answered, never acted on.
Put everything the other machine needs into the question: it cannot see this chat or your files.

Prints one of:
    ANSWER from <agent> (<staff>):   then the answer. Relay it to Zaim and say who answered.
    WAITING id=<id>                  not answered within --wait seconds. Tell Zaim, then `get <id>`.
    LOCAL: ...                       that staff member's work runs on THIS machine: do it here.
    NO LINK: ...                     this machine has no Mission Control link (MatDuo itself has none).
    LIMIT / FAILED / ERROR: ...      say so to Zaim; do not make up an answer.

The link (address and key) is read from this machine's Mission Control bridge settings file. The
key is sent only to that address and is never printed. $MAHAREKA_MC_ENV names the file directly.
Standard library only.
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.request
from pathlib import Path

DESKS = ("cos", "lead", "convert", "qs", "design", "pm", "admin", "finance", "legal")

def read_env(path):
    out = {}
    try:
        for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$", line)
            if m: out[m.group(1)] = m.group(2).strip().strip("'\"")
    except OSError:
        pass
    return out

def find_link():
    """(base url, key) from this machine's bridge settings, or None. The agent that runs tasks is preferred."""
    named = os.environ.get("MAHAREKA_MC_ENV")
    files = [Path(named).expanduser()] if named else sorted((Path.home() / "mahareka-mission-control" / "deploy").glob("*.env"))
    found = []
    for f in files:
        e = read_env(f)
        url, key = e.get("MC_INGEST_URL", ""), e.get("MC_BRIDGE_TOKEN", "")
        m = re.match(r"^(https?)://([^/\s]+)", url)
        if not m or len(key) < 32: continue
        host = m.group(2).split(":")[0]
        if m.group(1) != "https" and host not in ("127.0.0.1", "localhost"): continue      # the key only travels over https
        runs = e.get("MC_RUN_TASKS", "").lower() in ("1", "true", "yes") and e.get("HERMES_USE_CLI", "true").lower() != "false"
        found.append((0 if runs else 1, f"{m.group(1)}://{m.group(2)}", key))
    return sorted(found)[0][1:] if found else None

def call(base, key, method, path, body=None):
    """(status, json). Network trouble → (0, {error})."""
    req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode("utf-8") if body is not None else None,
                                 headers={"authorization": f"Bearer {key}", "content-type": "application/json", "accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except ValueError: return e.code, {"error": f"Mission Control answered {e.code}."}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return 0, {"error": f"Mission Control could not be reached ({type(e).__name__})."}

def wait_for(base, key, ask_id, seconds):
    end = time.time() + max(0, seconds)
    while True:
        st, j = call(base, key, "GET", f"/api/bridge/ask?id={ask_id}")
        if st == 200 and j.get("status") == "answered":
            print(f"ANSWER from {j.get('answeredBy', 'the other agent')}:\n{j.get('answer', '')}"); return 0
        if st == 200 and j.get("status") == "failed":
            print(f"FAILED: {j.get('error', 'the question was not answered')}"); return 4
        if st not in (0, 200):
            print(f"ERROR: {j.get('error', st)}"); return 5
        if time.time() >= end:
            print(f"WAITING id={ask_id}: not answered yet. Tell Zaim it is with the other agent, then run: ask_master.py get {ask_id}"); return 0
        time.sleep(6)

def main():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"): s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Ask a staff member on another machine, through Mission Control.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask"); a.add_argument("--desk", default="qs", choices=DESKS); a.add_argument("--wait", type=int, default=240)
    a.add_argument("question", help='the whole question, or "-" to read it from standard input')
    g = sub.add_parser("get"); g.add_argument("id"); g.add_argument("--wait", type=int, default=120)
    args = ap.parse_args()
    link = find_link()
    if not link:
        print("NO LINK: this machine has no Mission Control bridge link. If this is the master (MatDuo), do the work here."); return 2
    base, key = link
    if args.cmd == "get":
        if not re.match(r"^[0-9a-fA-F-]{36}$", args.id): print("ERROR: that is not a question id."); return 5
        return wait_for(base, key, args.id, args.wait)
    question = sys.stdin.read() if args.question == "-" else args.question
    st, j = call(base, key, "POST", "/api/bridge/ask", {"desk": args.desk, "question": question})
    if st == 201:
        print(f"ASKED id={j['id']} · {j.get('staff', args.desk)} on {j.get('answeredBy', 'the other agent')}")
        return wait_for(base, key, j["id"], args.wait)
    if st == 409 and j.get("code") == "local": print(f"LOCAL: {j.get('error')}"); return 3
    if st == 429: print(f"LIMIT: {j.get('error')}"); return 6
    if st == 401: print("NO LINK: Mission Control did not accept this machine's key."); return 2
    print(f"ERROR: {j.get('error', st)}"); return 5

if __name__ == "__main__":
    sys.exit(main())
