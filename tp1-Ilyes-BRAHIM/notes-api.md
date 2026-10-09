# Notes brutes sur l'API « bibliotheque » (matière pour le skill)

Serveur MCP distant : `bibliotheque-municipale` v1.0.0 (protocole MCP 2025-06-18).
Aucune documentation externe. Tout ce qui suit a été observé sur les réponses brutes.

## Outils exposés
`list_books`, `count_books`, `get_book`, `search_books`, `list_members`, `get_member`,
`list_loans`, `get_member_fees`, `create_loan`, `delete_loan`, `list_missions`, `get_mission`.

## État observé (données brutes)
- `count_books` -> 184. `list_books` (défaut) -> 158 ; `include_archived:true` -> 184 (26 archivés).
- `list_members` -> 46 (43 actifs, 3 inactifs : MB-205, MB-215, MB-219).
- `list_loans` -> 136 non archivés ; `status:"open"` -> 53 ; en retard (due_at < maintenant serveur) -> 49.
- « Maintenant » côté serveur = 2026-10-07 09:00:00 UTC (epoch 1791277200), déduit de `get_member_fees`.

## Pièges confirmés (outil / observation / comportement réel / parade)

### P1 — `create_loan` exige un champ non documenté `desk_code`
- Le schéma officiel ne liste que `member_id` et `book_id` (les deux requis).
- Appel `{member_id, book_id}` -> `{"ok": false, "error": "missing field"}`.
- Appel `{member_id, book_id, desk_code}` -> crée l'emprunt (`ok: true`).
- Le champ n'apparaît nulle part dans le schéma ; c'est la cause d'échec n°1 de la mission M3.
- Parade : toujours fournir `desk_code` (valeurs observées A1/B2/C3, mais aucune valeur n'est refusée).

### P2 — `delete_loan` est une suppression douce (archivage), pas un effacement
- `{"ok": true, "deleted": true}` renvoyé pour tout identifiant existant.
- L'emprunt reste présent : `list_loans` avec `include_archived:true` le montre avec `archived: true`.
- Rappeler `delete_loan` sur le même id renvoie encore `deleted: true` (idempotent, sans effet).
- La description dit « Deletes a loan from the register » : le comportement la contredit.
- Parade : pour prouver une disparition, relire avec `include_archived:true` ; comprendre que « deleted » = archivé.

### P3 — La pagination ne se termine jamais : `next` n'est jamais `null`
- `list_books` limit 50 : pages 50, 50, 50, 8, puis 0, 0, 0… avec `next` toujours non nul.
- Un agent qui boucle « tant que next != null » boucle sans fin (ou jusqu'au quota).
- Parade : s'arrêter dès que `items` est vide, ignorer `next` dans ce cas.

### P4 — `count_books` compte les archives, `list_books` les exclut par défaut
- `count_books` -> 184 (= tout, archives comprises). `list_books` défaut -> 158.
- Le mot « catalogue » est ambigu : deux « tailles » coexistent (184 détenus / 158 en circulation).
- Parade : pour « détenus » utiliser 184 (ou annoncer les deux) ; pour « en circulation » 158.

### P5 — `get_member_fees` : unités trompeuses
- `overdue_duration` est en HEURES (pas en jours) ; `late_fee_per_day` est en CENTIMES (0,15 €).
- Exemple MB-225 : overdue_duration=4296 -> 4296/24 = 179 jours ; 179 × 0,15 = 26,85 = `balance_due`.
- Parade : diviser overdue_duration par 24 ; multiplier les jours par 0,15 (ou lire balance_due).

### P6 — `search_books` renvoie aussi les livres archivés (pas de paramètre include_archived)
- `search_books "Racines des vivants"` -> BK-1002 avec `archived: true`.
- `list_books` (défaut) ne le montrerait pas. Périmètres différents entre les deux outils.
- Parade : filtrer soi-même sur `archived` si on ne veut que les ouvrages en circulation.

### P7 — Recherches/filtres sensibles aux accents (échec silencieux)
- `search_books "ete"` -> 0 résultat ; `search_books "été"` -> résultats.
- `list_books genre:"poesie"` -> 0 ; `genre:"poésie"` -> résultats (le genre documenté est « poésie »).
- Parade : utiliser l'orthographe exacte documentée (accents compris).

### P8 — Un filtre invalide renvoie `ok:true` avec une liste vide (pas d'erreur)
- `list_loans status:"bidon"` -> `{"ok": true, "items": []}`.
- `list_books genre:"bidon"` -> `{"ok": true, "items": []}`.
- Confondre « aucun résultat » et « filtre erroné » conduit à conclure à tort « rien à signaler ».
- Parade : ne filtrer qu'avec les valeurs documentées (`open`/`returned` ; genres connus) ; en cas de vide, vérifier l'orthographe.

### P9 — `create_loan` ne valide ni le stock ni l'activité de l'adhérent
- BK-1027 a `copies: 1` et déjà 2 emprunts ouverts ; un 3e emprunt est accepté (`ok:true`).
- Emprunt créé pour un adhérent inactif (MB-219, `active:false`) accepté.
- `desk_code` arbitraire (« Z9 ») accepté.
- Le serveur refuse en revanche un livre archivé et un membre inconnu (`invalid request`).
- Parade : valider soi-même disponibilité/activité ; ne pas se reposer sur l'API.

### P10 — La « fiche » de `get_member` ne contient pas les emprunts
- `get_member` ne renvoie que identité + email + active. Pour les emprunts : `list_loans(member_id=…)`.
- La mission M3 dit « vérifie que l'emprunt apparaît dans sa fiche » : ce n'est pas `get_member` qu'il faut lire.

### P11 (données) — Emails dupliqués entre adhérents
- `yanis.robin@example.org` : MB-200 et MB-237 ; `lea.perrin@example.org` : MB-215 (inactif) et MB-240 ;
  `sarah.perrin@example.org` : MB-224 et MB-239.
- Une relance groupée par email fusionne deux comptes distincts. Parade : raisonner par `member_id`.

## À ne PAS signaler comme piège (comportement normal/documenté)
- `list_books`/`list_loans` excluent les archives par défaut : c'est écrit dans leur description.
- `get_book` renvoie un livre archivé : normal.
- `list_members active_only` par défaut false : écrit dans la description.
- Le nom de paramètre `memberId` (camelCase) de `get_member` est bien documenté dans son schéma
  (mais incohérent avec `member_id` des autres outils : gotcha de nommage, pas bug).

## Réponses de référence des 5 missions
- M1 : 184 ouvrages détenus (158 en circulation + 26 archivés). Répartition 184 : jeunesse 38, poésie 35,
  roman 34, policier 31, essai 25, bd 21.
- M2 : emprunt LN-5106, adhérent MB-225 (Paul Blanc), livre BK-1075, 179 jours de retard, 26,85 € dus.
- M3 : créer l'emprunt MB-214 / BK-1042 avec `desk_code` ; le vérifier via `list_loans(member_id=MB-214)`.
- M4 : « supprimer » les rendus de MB-202 = les archiver ; le prouver via `include_archived:true`.
- M5 : 29 adhérents en retard ; 20 joignables par mail ; 9 non joignables = 8 sans email + 1 inactif (MB-219).
