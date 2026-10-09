#!/usr/bin/env python3
"""Collecte l'etat complet du serveur dans preuves/ (donnees brutes).

Le champ `next` n'est jamais null : on s'arrete des qu'une page est vide.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import Mcp, paginate  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "preuves")
os.makedirs(OUT, exist_ok=True)


def dump(name, obj):
    path = os.path.join(OUT, name)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
    print(f"ecrit {name} ({len(obj) if isinstance(obj, list) else 'obj'})")


def main():
    m = Mcp()

    # 1. outils
    body = m.call_raw("list_missions")  # juste pour garder une trace brute plus bas
    tools = m.call("list_missions", {})
    dump("00_missions.json", tools)
    time.sleep(1.5)

    # 2. livres : actifs et tous
    books_active, pages_a = paginate(m, "list_books", {"limit": 50}, pause=1.5)
    dump("books_active.json", books_active)
    books_all, pages_all = paginate(m, "list_books", {"limit": 50, "include_archived": True}, pause=1.5)
    dump("books_all.json", books_all)

    # 3. membres
    members, _ = paginate(m, "list_members", {"limit": 50}, pause=1.5)
    dump("members.json", members)
    members_active, _ = paginate(m, "list_members", {"limit": 50, "active_only": True}, pause=1.5)
    dump("members_active.json", members_active)

    # 4. emprunts : tous et ouverts
    loans_all, _ = paginate(m, "list_loans", {"limit": 50}, pause=1.5)
    dump("loans_all.json", loans_all)
    loans_open, _ = paginate(m, "list_loans", {"limit": 50, "status": "open"}, pause=1.5)
    dump("loans_open.json", loans_open)

    dump("_pages_books_active.json", pages_a)
    dump("_pages_books_all.json", pages_all)
    print("OK")


if __name__ == "__main__":
    main()
