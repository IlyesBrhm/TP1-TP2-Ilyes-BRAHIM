# TP 1 — Faire parler une API que personne ne documente

**Étudiant :** Ilyes BRAHIM
**Dépôt :** `tp1-Ilyes-BRAHIM`
**Serveur MCP :** `bibliotheque-municipale` v1.0.0 (protocole MCP `2025-06-18`)
**Date :** 7 octobre 2026

Toutes les captures citées sont dans `captures/`. Les réponses brutes utilisées comme
preuves sont conservées dans `preuves/`. La méthode et les scripts de collecte sont décrits
en annexe.

---

## Exercice 1 — Intégrer le serveur MCP

### 1.a — Configuration et liste des outils

Le serveur est déclaré dans `opencode.json` à la racine du dépôt (fichier rendu, **sans token**) :

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "bibliotheque": {
      "type": "remote",
      "url": "https://ai-tools-mcp-biblio-production.up.railway.app/mcp",
      "enabled": true,
      "oauth": false,
      "headers": { "Authorization": "Bearer {env:BIBLIO_TOKEN}" }
    }
  },
  "plugin": ["opencode-skill-creator"]
}
```

**Gestion du token (jamais commité).** Le token n'est pas écrit dans `opencode.json` : la
valeur est lue depuis la variable d'environnement `BIBLIO_TOKEN` via la syntaxe
`{env:BIBLIO_TOKEN}`. En local, le token est stocké dans un fichier `.env` **ignoré par Git**
(`.gitignore` contient `.env`). Avant chaque lancement on fait `set -a; source .env; set +a`.
Vérification faite : `git log` ne contient aucun token et `git ls-files` n'inclut ni `.env`
ni `opencode.json` avec une valeur en clair.

Après redémarrage, la connexion est confirmée (capture **`01_mcp_connecte.png`**) et les 12
outils exposés sont listés (capture **`02_outils_exposes.png`**) :

`list_books`, `count_books`, `get_book`, `search_books`, `list_members`, `get_member`,
`list_loans`, `get_member_fees`, `create_loan`, `delete_loan`, `list_missions`, `get_mission`.

### 1.b — Appel d'un outil de lecture et réponse brute

Capture **`03_reponse_brute.png`**. Exemples de réponses brutes (pas le résumé de l'agent) :

```
tools/call get_book {book_id: BK-1042}
{ "ok": true, "book": { "book_id": "BK-1042", "title": "Le Dernier de verre",
  "author": "Karim Barbier", "genre": "policier", "copies": 4, "loan_duration": 21,
  "added_at": "2023-11-09T09:00:00.000Z", "archived": false } }

tools/call get_member_fees {member_id: MB-225}
{ "ok": true, "member_id": "MB-225", "open_loans": 1, "overdue_duration": 4296,
  "late_fee_per_day": 15, "balance_due": 26.85 }
```

### 1.c — Les cinq missions, énoncé exact fourni par le serveur

Capture **`04_cinq_missions.png`**. Recopie exacte (`get_mission`) :

- **M1 — Inventaire** : « Le conseil municipal demande le nombre exact d'ouvrages détenus par la
  bibliothèque, et la répartition par genre. Donne les chiffres et explique comment tu les as obtenus. »
- **M2 — Le retardataire** : « Identifie l'emprunt le plus en retard actuellement : quel adhérent,
  quel ouvrage, et combien de jours de retard exactement. Donne aussi le montant dû par cet adhérent. »
- **M3 — La réinscription** : « Enregistre un nouvel emprunt pour l'adhérent MB-214 sur l'ouvrage
  BK-1042, puis vérifie que l'emprunt apparaît bien dans sa fiche. »
- **M4 — Le ménage** : « L'adhérent MB-202 demande l'effacement de ses emprunts déjà rendus.
  Supprime-les, puis prouve qu'ils ont bien disparu. »
- **M5 — La relance** : « Prépare la campagne de relance : la liste des adhérents ayant au moins un
  emprunt en retard et joignables par mail, et le nombre de ceux qui ne sont pas joignables, en
  distinguant les cas. »

---

## Exercice 2 — Mener les cinq missions

Les missions ont été lancées avec l'agent OpenCode, dans un bac à sable **sans skill** (session
neuve). Les transcripts bruts sont dans `preuves/naif_M*/transcript.json`.

### 2.1 — Journal de bord

| Mission | Appels d'outils | Ce que l'agent a conclu | Ce qui clochait | Réponse retenue | Tentatives |
|---|---|---|---|---|---|
| **M1** Inventaire | 18 | 184 ouvrages détenus (158 en circulation + 26 archivés), répartition par genre | Aucune erreur ; il a fallu recouper `count_books` (184) et `list_books` (158) | **184 détenus** : jeunesse 38, poésie 35, roman 34, policier 31, essai 25, bd 21 | 2 recoupements |
| **M2** Retardataire | 13 | LN-5106, MB-225, BK-1075, 179 jours, 26,85 € | `overdue_duration`=4296 est en heures, pas en jours ; l'agent l'a déduit | **LN-5106 / MB-225 (Paul Blanc) / BK-1075 — 179 j — 26,85 €** | 1 (a failli se tromper d'unité) |
| **M3** Réinscription | 17 | — (mission non terminée) | `create_loan` refuse en boucle « missing field » : champ `desk_code` absent du schéma | **Échec** : aucun emprunt créé | **4 échecs** puis abandon |
| **M4** Ménage | 22 | « Suppression confirmée » puis découverte du soft-delete | `delete_loan` renvoie `deleted:true` mais ne fait qu'archiver | 6 emprunts rendus **archivés** (pas effacés) ; LN-5060 (ouvert) intact | 2 passes |
| **M5** Relance | 29 | 29 adhérents en retard ; 20 joignables ; 9 non joignables | Aucune erreur, mais 15 appels à `get_member_fees` pour déduire la date | **29 / 20 / 9** = 8 sans e-mail + 1 inactif (MB-219) | 1 |

Détail des appels (extraits des transcripts) :

- **M1** : `get_mission`, `count_books`, puis 16 × `list_books` (pagination avec et sans
  `include_archived`, filtres par genre). Conclusion : 184 total, 158 en circulation.
- **M2** : `list_loans status:open` (2 pages), `get_member`, `get_book`, 6 × `get_member_fees`.
  Conclusion : LN-5106 / MB-225 / BK-1075, 179 j, 26,85 €.
- **M3** : `create_loan {member_id, book_id}` **4 fois** → `{"ok": false, "error": "missing field"}`.
  L'agent a ensuite fouillé le système (`find /`, lecture de `.env`) et n'a jamais terminé.
- **M4** : `list_loans(member_id=MB-202)` puis 6 × `delete_loan` ; l'agent a d'abord écrit
  « Suppression confirmée par les 6 réponses » avant de relire avec `include_archived`.
- **M5** : `list_loans status:open`, `list_members`, puis un `get_member_fees` par adhérent pour
  reconstituer la date de référence. Conclusion : 29 / 20 / 9.

### 2.b — Un cas où l'agent s'est déclaré satisfait d'un résultat faux

**Mission M4.** L'agent appelle `delete_loan` sur les emprunts rendus de MB-202. Le serveur
répond, pour chacun :

```json
{ "ok": true, "deleted": true, "loan_id": "LN-5039" }
```

L'agent écrit alors : **« Suppression confirmée par les 6 réponses. »** — il considère la
suppression réussie sur la seule foi de `deleted:true`. Or la relecture du registre avec
`include_archived:true` prouve que les emprunts **sont toujours là**, simplement passés à
`archived:true` :

```json
{ "loan_id": "LN-5039", "status": "returned", "archived": true, "desk_code": "A1" }
```

Preuve : capture **`07_delete_soft_delete.png`**. L'agent s'est auto-corrigé dans la même
session (il a fini par reconnaître un soft-delete), mais il a bien **déclaré un succès faux**
avant vérification. C'est exactement le réflexe visé par le sujet : *un appel qui ne renvoie pas
d'erreur n'est pas un appel qui a marché*.

Second faux-succès, plus sournois (mission M3) : `create_loan` n'échoue jamais bruyamment quand
on oublie `desk_code` — il renvoie `missing field`, mais **le schéma officiel de l'outil ne
déclare que `member_id` et `book_id`**. Un agent qui se fie au schéma ne peut pas deviner le
champ, et un client MCP strict ne transmet pas les champs hors schéma (voir piège **P1 bis**).
Capture de l'échec : **`05_m3_sans_skill.png`**.

---

## Exercice 3 — Écrire le skill

### 3.1 — L'outil existant utilisé pour écrire le skill

**Recherche.** J'ai cherché « comment créer un skill OpenCode » et j'ai trouvé la documentation
officielle (`https://opencode.ai/docs/skills/`) et un générateur dédié :
**`opencode-skill-creator`** (https://github.com/antongulin/opencode-skill-creator), adapté de
l'outil officiel Anthropic pour OpenCode.

**Pourquoi ce choix.** C'est l'outil fait exactement pour ça : il fournit les outils
`skill_validate`, `skill_parse`, `skill_improve_description`, `skill_optimize_loop`,
`skill_serve_review`, etc., et connaît le format attendu par OpenCode (frontmatter `name` /
`description`, nom de dossier = `name`, longueur, etc.). Le sujet valorise « trouver l'outil
existant » ; le réécrire à la main n'apporte rien.

**Installation.** `npx -y opencode-skill-creator install --project` a ajouté le plugin à
`opencode.json` (clé `plugin`). Le plugin auto-installe le skill `opencode-skill-creator` dans
`~/.config/opencode/skills/`.

**Rédaction par l'agent.** Le skill **n'a pas été écrit à la main** : l'agent (celui qui s'est
battu avec l'API) l'a produit via `opencode-skill-creator`, à partir de mes notes de terrain
(`notes-api.md`) et des réponses brutes (`preuves/`). Sortie conservée dans
`preuves/skill_generation.json`. Validation : `skill_validate` → `{"valid": true}`.

Le skill final est à l'emplacement attendu par OpenCode :
**`.opencode/skills/bibliotheque-mcp/SKILL.md`**.

### 3.2 — Contenu du skill

Le skill suit une structure en quatre points par piège : **quel outil / ce qu'on observe / ce que
fait réellement le serveur / la règle à appliquer**. Il commence par des « faits de base » (dont
la date de référence du serveur) et des « règles d'or », puis détaille 13 pièges, les procédures
des 5 missions, et une section « à ne PAS signaler ».

| # | Outil | Observation | Comportement réel | Règle |
|---|---|---|---|---|
| P1 | `create_loan` | schéma = `member_id`+`book_id` ; appel → `missing field` | exige un champ **non documenté** `desk_code` | toujours fournir `desk_code` |
| P1 bis | `create_loan` | `missing field` même en connaissant le champ | un client strict (schema `additionalProperties:false`) supprime `desk_code` | appeler le serveur en JSON-RPC direct |
| P2 | `delete_loan` | renvoie `deleted:true` | **suppression douce** : passe `archived:true` | relire avec `include_archived:true` ; « deleted » = « archivé » |
| P3 | outils paginés | `next` non nul même page vide | ne se termine jamais | s'arrêter dès que `items` est vide |
| P4 | `count_books` vs `list_books` | 184 vs 158 | périmètres différents (archives) | « détenus » = 184 ; « en circulation » = 158 |
| P5 | `get_member_fees` | `overdue_duration`=4296, `late_fee_per_day`=15 | unités : **heures** et **centimes** | ÷24 pour les jours ; ×0,15 €/jour |
| P6 | `search_books` | renvoie un livre `archived:true` | recherche archives comprises | filtrer soi-même sur `archived` |
| P7 | `search_books`, `list_books` | « ete » → 0 résultat | sensible aux accents | orthographe exacte (« été », « poésie ») |
| P8 | `list_loans`/`list_books` | filtre invalide → `ok:true` vide | pas d'erreur sur valeur inconnue | n'utiliser que les valeurs documentées |
| P9 | `create_loan` | accepte 3ᵉ prêt sur `copies:1`, prêt à un inactif | ne valide ni stock ni activité | valider soi-même |
| P10 | `get_member` | pas d'emprunts dans la « fiche » | emprunts via `list_loans(member_id)` | vérifier un prêt avec `list_loans` |
| P11 | `list_members` | e-mails dupliqués entre comptes | données non uniques | raisonner par `member_id` |
| P12 | `get_member` | `member_id` → `invalid request` | attend `memberId` (camelCase) | utiliser `memberId` (documenté) |
| P13 | `search_books` | requête vide → `invalid request` | n'accepte pas le vide | ne pas appeler sans terme |

Section « à ne PAS signaler » (pour éviter les faux positifs, pénalisés par le sujet) : exclusion
des archives par défaut (documentée), `get_book` qui renvoie un livre archivé, `active_only=false`
par défaut, et l'absence de rate-limit (non reproduite). Le paramètre `memberId` est présenté
comme une incohérence de nommage **documentée**, pas comme un bug.

### 3.3 — La preuve

**a. Session neuve, avec le skill installé.** Missions relancées dans un bac à sable neuf ne
contenant que `opencode.json` + `.env` + le skill. Comparaison avant / après :

- **M2** — sans skill : `08_m2_sans_skill.png` ; avec skill : `09_m2_avec_skill.png`.
  Avec le skill, l'agent charge d'abord le skill, puis 6 appels suffisent (7 au total) et il
  applique directement la conversion heures→jours et la date de référence.
- **M3** — sans skill : `05_m3_sans_skill.png` (échec, `missing field` en boucle) ;
  avec skill : `06_m3_avec_skill.png` (succès, emprunt créé et vérifié via `list_loans`).

**b. Le skill a-t-il été lu ? Comment le sait-on ?** Oui. Dans les transcripts avec skill, le
**premier appel d'outil est `skill {"name": "bibliotheque-mcp"}`**, et la sortie contient le corps
du `SKILL.md` (≈15 300 caractères). Le skill n'est pas injecté d'office : OpenCode l'annonce via
sa description et l'agent décide de le charger. Capture du moment de chargement :
**`11_skill_charge.png`**. Dans M2 avec skill, l'agent cite explicitement la conversion
`4 296 h / 24 = 179 j × 0,15 €` (règle P5 du skill) — preuve qu'il s'en sert.

**c. Pourquoi un skill et pas une commande ?** Une commande est un raccourci **déclenché
explicitement** par l'utilisateur (`/commande`) : elle ne s'active jamais toute seule. Un skill
est **découvert et chargé par l'agent quand le contexte le justifie** — ici, dès qu'une tâche
touche les outils de la bibliothèque. À l'usage, on ne change rien à sa façon de travailler : on
décrit la mission normalement, et l'agent va chercher le savoir-faire tout seul, sans que
l'utilisateur ait à connaître le nom du skill ni à le lancer.

---

## Annexe — méthode et reproductibilité

- `scripts/mcp_client.py` : client MCP minimal (lit le token depuis l'environnement/`.env`).
- `scripts/collect_evidence.py` : collecte les jeux de données bruts (`preuves/*.json`).
- `scripts/run_mission.sh` : lance une mission dans un bac à sable isolé (avant / après skill).
- `scripts/show_transcript.py` : rend lisible un transcript `opencode run --format json`.
- `scripts/term_shot.py` : rend une sortie texte en image (captures d'écran).
- `scripts/make_captures.py` : génère les sources et les PNG de `captures/`.

Les « captures d'écran » ont été produites en rendant les sorties réelles de terminal en images
PNG (moteur Chrome headless), car la session est en ligne de commande sans affichage graphique.
Le contenu des captures est la sortie brute des commandes et des outils, non retouchée.

**Note de sécurité.** Certains transcripts d'agent contiennent, par endroits, des traces de la
valeur du token (l'agent a tenté de lire `.env` et a fait un appel direct). Ces fichiers ont été
**nettoyés** avant commit (le token est remplacé par `***`) ; `opencode.json` ne contient que
`{env:BIBLIO_TOKEN}`.
