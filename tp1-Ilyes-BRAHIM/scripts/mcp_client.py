#!/usr/bin/env python3
"""Client MCP minimal pour le serveur "bibliotheque".

Le token n'est jamais écrit dans ce fichier : il est lu depuis la variable
d'environnement BIBLIO_TOKEN (voir .env, ignoré par git) ou depuis .env.

Usage:
    python3 scripts/mcp_client.py <outil> '<json-args>'
    python3 scripts/mcp_client.py --raw <outil> '<json-args>'   # réponse brute complète
"""
import json
import os
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_env():
    env = {}
    path = os.path.join(REPO, ".env")
    if os.path.exists(path):
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


def _config():
    with open(os.path.join(REPO, "opencode.json")) as fh:
        cfg = json.load(fh)
    return cfg["mcp"]["bibliotheque"]


class Mcp:
    def __init__(self):
        cfg = _config()
        self.url = cfg["url"]
        env = _load_env()
        self.token = os.environ.get("BIBLIO_TOKEN") or env.get("BIBLIO_TOKEN")
        if not self.token:
            raise SystemExit("BIBLIO_TOKEN manquant (exportez-le ou mettez-le dans .env)")
        self.session = None
        self._init()

    def _post(self, payload):
        data = json.dumps(payload).encode()
        req = urllib.request.Request(self.url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        req.add_header("Authorization", f"Bearer {self.token}")
        if self.session:
            req.add_header("Mcp-Session-Id", self.session)
        with urllib.request.urlopen(req, timeout=30) as resp:
            self.session = resp.headers.get("Mcp-Session-Id", self.session)
            return resp.read().decode()

    @staticmethod
    def _sse_json(body):
        for line in body.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:])
        return None

    def _init(self):
        body = self._post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "tp1-client", "version": "1.0"}},
        })
        self._sse_json(body)

    def call(self, tool, args=None):
        args = args or {}
        payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                   "params": {"name": tool, "arguments": args}}
        body = self._post(payload)
        msg = self._sse_json(body)
        if msg is None:
            return {"_raw_sse": body}
        if "error" in msg:
            return {"_error": msg["error"]}
        text = msg["result"]["content"][0]["text"]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"_text": text}

    def call_raw(self, tool, args=None):
        """Renvoie la réponse brute (texte de la SSE) telle quelle."""
        args = args or {}
        payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                   "params": {"name": tool, "arguments": args}}
        return self._post(payload)


def paginate(mcp, tool, base_args, max_pages=200, pause=0.0):
    """Pagine en s'arrêtant quand la page est vide (le champ `next` ment)."""
    items, start, pages = [], None, []
    for _ in range(max_pages):
        args = dict(base_args)
        if start:
            args["start_key"] = start
        r = mcp.call(tool, args)
        page = r.get("items", [])
        pages.append({"start_key": start, "n": len(page), "next": r.get("next"), "ok": r.get("ok")})
        items.extend(page)
        if not page:  # page vide -> fin, même si `next` est non nul
            break
        start = r.get("next")
        if not start:
            break
        if pause:
            time.sleep(pause)
    return items, pages


if __name__ == "__main__":
    argv = sys.argv[1:]
    raw = False
    if argv and argv[0] == "--raw":
        raw = True
        argv = argv[1:]
    tool = argv[0]
    args = json.loads(argv[1]) if len(argv) > 1 else {}
    client = Mcp()
    if raw:
        print(client.call_raw(tool, args))
    else:
        print(json.dumps(client.call(tool, args), indent=2, ensure_ascii=False))
