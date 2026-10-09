#!/usr/bin/env python3
"""Genere les sources de captures puis les rend en PNG (via term_shot.py)."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import Mcp  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "captures", "src")
CAP = os.path.join(REPO, "captures")
os.makedirs(SRC, exist_ok=True)


def write(name, text):
    with open(os.path.join(SRC, name), "w", encoding="utf-8") as fh:
        fh.write(text)


def read(name):
    with open(name, encoding="utf-8") as fh:
        return fh.read()


def last_text(path):
    last = ""
    for raw in open(path):
        raw = raw.strip()
        if not raw:
            continue
        ev = json.loads(raw)
        if ev.get("type") == "text":
            last = ev["part"].get("text", "")
    return last


def tool_lines(path, keep=None):
    out = []
    for raw in open(path):
        raw = raw.strip()
        if not raw:
            continue
        ev = json.loads(raw)
        if ev.get("type") == "tool_use":
            p = ev["part"]
            tool = p.get("tool")
            inp = json.dumps(p.get("state", {}).get("input", {}), ensure_ascii=False)
            out.append(f"$ {tool} {inp}")
    return "\n".join(out)


def skill_loaded_lines(path):
    for raw in open(path):
        raw = raw.strip()
        if not raw:
            continue
        ev = json.loads(raw)
        if ev.get("type") == "tool_use" and ev["part"].get("tool") == "skill":
            out = ev["part"].get("state", {}).get("output", "")
            return (f'> opencode : l\'agent appelle l\'outil skill\n\n'
                    f'$ skill {{"name": "bibliotheque-mcp"}}\n\n'
                    f'--- extrait du contenu charge ({len(out)} caracteres) ---\n'
                    + out[:900])
    return ""


def render(src_name, out_name, title):
    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "term_shot.py"),
                    "--out", os.path.join(CAP, out_name), "--title", title,
                    "--file", os.path.join(SRC, src_name)], check=True)


def main():
    m = Mcp()

    # 03 reponse brute avec de vraies donnees
    b = m.call("get_book", {"book_id": "BK-1042"})
    fees = m.call("get_member_fees", {"member_id": "MB-225"})
    write("03_reponse_brute.txt",
          "tools/call get_book {book_id: BK-1042}\n" + json.dumps(b, indent=2, ensure_ascii=False)
          + "\n\ntools/call get_member_fees {member_id: MB-225}\n"
          + json.dumps(fees, indent=2, ensure_ascii=False))

    # 04 les cinq missions (enonce exact du serveur)
    lines = ["tools/call list_missions  ->  puis get_mission M1..M5\n"]
    for mid in ["M1", "M2", "M3", "M4", "M5"]:
        r = m.call("get_mission", {"mission_id": mid})
        ms = r["mission"]
        lines.append(f'{ms["mission_id"]} — {ms["title"]}')
        lines.append(f'    "{ms["brief"]}"')
        lines.append("")
    write("04_missions.txt", "\n".join(lines))

    # 05 M3 sans skill (echec)
    write("05_m3_avant.txt",
          "MISSION M3 — SANS SKILL (extrait du transcript brut)\n\n"
          + tool_lines(os.path.join(REPO, "preuves/naif_M3b/transcript.json"))
          + "\n\n=> create_loan renvoie 'missing field' en boucle : mission non terminee.")

    # 06 M3 avec skill (succes)
    write("06_m3_apres.txt",
          "MISSION M3 — AVEC SKILL (extrait)\n\n"
          + tool_lines(os.path.join(REPO, "preuves/avec_skill_M3b/transcript.json"))
          + "\n\nREPONSE FINALE :\n" + last_text(os.path.join(REPO, "preuves/avec_skill_M3b/transcript.json")))

    # 07 delete_loan faux succes
    write("07_delete_soft.txt", read(os.path.join(REPO, "preuves/H_delete_soft.txt"))[:2600])

    # 08 M2 sans skill
    write("08_m2_avant.txt",
          "MISSION M2 — SANS SKILL\n\n" + last_text(os.path.join(REPO, "preuves/naif_M2b/transcript.json")))

    # 09 M2 avec skill + chargement
    write("09_m2_apres.txt",
          "MISSION M2 — AVEC SKILL\n\n"
          + skill_loaded_lines(os.path.join(REPO, "preuves/avec_skill_M2/transcript.json"))
          + "\n\nREPONSE FINALE :\n"
          + last_text(os.path.join(REPO, "preuves/avec_skill_M2/transcript.json")))

    # 10 pagination
    write("10_pagination.txt", read(os.path.join(REPO, "preuves/B_pagination.txt")))

    # 11 moment de chargement du skill (M3)
    write("11_skill_charge.txt",
          "MOMENT OU OPENCODE CHARGE LE SKILL (mission M3 avec skill)\n\n"
          + skill_loaded_lines(os.path.join(REPO, "preuves/avec_skill_M3b/transcript.json")))

    pairs = [
        ("01_mcp_list.txt", "01_mcp_connecte.png", "opencode mcp list — serveur MCP connecte"),
        ("02_outils.txt", "02_outils_exposes.png", "Outils exposes par le serveur MCP (tools/list)"),
        ("03_reponse_brute.txt", "03_reponse_brute.png", "Reponses brutes avec de vraies donnees"),
        ("04_missions.txt", "04_cinq_missions.png", "Enonce exact des cinq missions (fourni par le serveur)"),
        ("05_m3_avant.txt", "05_m3_sans_skill.png", "Mission M3 SANS skill — echec"),
        ("06_m3_apres.txt", "06_m3_avec_skill.png", "Mission M3 AVEC skill — succes"),
        ("07_delete_soft.txt", "07_delete_soft_delete.png", "delete_loan : deleted:true mais donnee conservee"),
        ("08_m2_avant.txt", "08_m2_sans_skill.png", "Mission M2 SANS skill"),
        ("09_m2_apres.txt", "09_m2_avec_skill.png", "Mission M2 AVEC skill"),
        ("10_pagination.txt", "10_pagination_next.png", "Pagination : next n'est jamais null"),
        ("11_skill_charge.txt", "11_skill_charge.png", "Chargement du skill par OpenCode"),
    ]
    for src, out, title in pairs:
        render(src, out, title)
    print("Captures generees dans", CAP)


if __name__ == "__main__":
    main()
