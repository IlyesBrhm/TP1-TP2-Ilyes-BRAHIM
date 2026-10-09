#!/usr/bin/env python3
"""Affiche lisiblement un transcript `opencode run --format json`."""
import json
import sys


def main(path, max_text=None):
    for raw in open(path):
        raw = raw.strip()
        if not raw:
            continue
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        part = ev.get("part", {})
        typ = ev.get("type")
        if typ == "tool_use":
            tool = part.get("tool")
            state = part.get("state", {})
            inp = state.get("input", {})
            out = state.get("output", "")
            if isinstance(out, (dict, list)):
                out = json.dumps(out, ensure_ascii=False)
            out = str(out)
            print(f"\n### OUTIL {tool}")
            print("  entree:", json.dumps(inp, ensure_ascii=False)[:500])
            if out:
                print("  sortie:", out[:900].replace("\n", "\n          "))
        elif typ == "text":
            txt = part.get("text", "")
            if max_text:
                txt = txt[:max_text]
            print(f"\n>>> TEXTE\n{txt}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
