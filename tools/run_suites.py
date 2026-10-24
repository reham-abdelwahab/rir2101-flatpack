#!/usr/bin/env python3
"""Run the regression suites headless and print pass counts.

Usage: python3 tools/run_suites.py [suite ...]
  suites: root, testing, v4.2.4 (default: all three)
Needs: pip install playwright; a Chrome/Chromium binary (CHROME env var, or
/opt/google/chrome/chrome, or Playwright's own browser). Serves the repo on
http://localhost:8765 for the duration of the run.
"""
import http.server, os, socketserver, sys, threading, functools
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8765
EXTRA = {}   # name → path?query, set from the command line as name=path
SUITES = {'root': 'tests/regress.html', 'testing': 'testing/tests/regress.html',
          'v4.2.4': 'v4.2.4/tests/regress.html'}


def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Q, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        srv = socketserver.ThreadingTCPServer(('127.0.0.1', PORT), h)
    except OSError:      # something already serves the repo on PORT (e.g. python3 -m http.server 8765): use it
        return None
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main(names):
    srv = serve()
    exe = os.environ.get('CHROME') or ('/opt/google/chrome/chrome' if os.path.exists('/opt/google/chrome/chrome') else None)
    ok_all = True
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe, args=['--no-sandbox'])
        for n in names:
            pg = b.new_page()
            pg.goto(f'http://localhost:{PORT}/{SUITES[n]}')
            pg.wait_for_function('window.REGRESS && window.REGRESS.done !== false && /ALL PASS|FAILURES|Harness crashed/.test(document.getElementById("out").innerText)', timeout=300_000)
            txt = pg.inner_text('#out')
            fails = [l for l in txt.splitlines() if l.startswith('FAIL')]
            summary = txt.strip().splitlines()[-1] if 'Harness crashed' not in txt else 'HARNESS CRASHED'
            print(f'{n:8s} {summary}')
            for f in fails:
                print('   ', f[:300])
            ok_all &= not fails
            pg.close()
        b.close()
    if srv: srv.shutdown()
    return 0 if ok_all else 1


if __name__ == '__main__':
    args = []
    for a in sys.argv[1:]:
        if '=' in a: k, v = a.split('=', 1); SUITES[k] = v; args.append(k)
        else: args.append(a)
    sys.exit(main(args or ['root', 'testing', 'v4.2.4']))
