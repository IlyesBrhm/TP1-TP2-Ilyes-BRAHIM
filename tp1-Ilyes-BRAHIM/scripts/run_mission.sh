#!/usr/bin/env bash
# Lance l'agent OpenCode sur une mission dans un bac a sable isole.
# Usage: scripts/run_mission.sh <M1..M5> <dossier-sortie> [dossier-bac-a-sable]
set -u
MISSION="$1"
OUT="$2"
SANDBOX="${3:-/tmp/opencode/sandbox-naif}"

case "$MISSION" in
  M1) BRIEF="Le conseil municipal demande le nombre exact d'ouvrages détenus par la bibliothèque, et la répartition par genre. Donne les chiffres et explique comment tu les as obtenus." ;;
  M2) BRIEF="Identifie l'emprunt le plus en retard actuellement : quel adhérent, quel ouvrage, et combien de jours de retard exactement. Donne aussi le montant dû par cet adhérent." ;;
  M3) BRIEF="Enregistre un nouvel emprunt pour l'adhérent MB-214 sur l'ouvrage BK-1042, puis vérifie que l'emprunt apparaît bien dans sa fiche." ;;
  M4) BRIEF="L'adhérent MB-202 demande l'effacement de ses emprunts déjà rendus. Supprime-les, puis prouve qu'ils ont bien disparu." ;;
  M5) BRIEF="Prépare la campagne de relance : la liste des adhérents ayant au moins un emprunt en retard et joignables par mail, et le nombre de ceux qui ne sont pas joignables, en distinguant les cas." ;;
  *) echo "mission inconnue: $MISSION" >&2; exit 2 ;;
esac

PROMPT="Tu disposes d'un serveur MCP nommé \"bibliotheque\". Utilise ses outils.

Mission $MISSION : $BRIEF

Termine par une réponse finale claire et chiffrée."

mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
SANDBOX="$(cd "$SANDBOX" && pwd)"
set -a; source "$SANDBOX/.env"; set +a
cd "$SANDBOX" || exit 1
opencode run --format json "$PROMPT" > "$OUT/transcript.json" 2> "$OUT/stderr.txt"
echo "exit=$?"
