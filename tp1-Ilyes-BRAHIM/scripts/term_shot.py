#!/usr/bin/env python3
"""Rend un texte (sortie de terminal) en image PNG « capture d'écran ».

Usage:
    python3 scripts/term_shot.py --out captures/nom.png --title "titre" < entree.txt
    python3 scripts/term_shot.py --out captures/nom.png --title "titre" --file entree.txt
"""
import argparse
import html
import os
import subprocess
import sys
import tempfile

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #0d1117; font-family: "DejaVu Sans Mono", monospace; }}
.bar {{ background: #161b22; padding: 10px 14px; border-bottom: 1px solid #30363d; }}
.dot {{ display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:7px; }}
.r {{ background:#ff5f56; }} .y {{ background:#ffbd2e; }} .g {{ background:#27c93f; }}
.title {{ color:#c9d1d9; font-size:13px; margin-left:10px; }}
pre {{ margin:0; padding:18px 20px; color:#c9d1d9; font-size:14px; line-height:1.5;
       white-space:pre-wrap; word-break:break-word; }}
</style></head><body>
<div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
<span class="title">{title}</span></div>
<pre>{body}</pre></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="terminal")
    ap.add_argument("--file")
    args = ap.parse_args()

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    page = HTML.format(title=html.escape(args.title), body=html.escape(text))

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(page)
        html_path = fh.name

    width = 1100
    lines = max(6, len(text.splitlines()))
    height = min(4000, 120 + lines * 22)
    subprocess.run([
        "google-chrome", "--headless", "--no-sandbox", "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={out}", f"file://{html_path}",
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(html_path)
    print(f"capture -> {args.out}")


if __name__ == "__main__":
    main()
