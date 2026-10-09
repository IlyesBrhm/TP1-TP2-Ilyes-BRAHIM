---
name: bibliotheque-mcp
description: "Guide opérationnel du serveur MCP « bibliotheque » (bibliothèque municipale) qui documente les pièges non documentés et les procédures de référence pour réussir les missions d'inventaire, de retard, d'emprunt, de suppression et de relance. Utilise ce skill SYSTÉMATIQUEMENT dès qu'une tâche touche les outils MCP bibliotheque (list_books, count_books, get_book, search_books, list_members, get_member, list_loans, get_member_fees, create_loan, delete_loan, list_missions, get_mission), même si l'utilisateur ne nomme pas le serveur : toute demande sur des ouvrages, adhérents, emprunts, retards, amendes ou relances de la bibliothèque municipale est concernée. Ce skill évite les faux positifs et les conclusions erronées."
---

# Serveur MCP « bibliotheque » — guide anti-pièges

Serveur MCP distant `bibliotheque-municipale` v1.0.0 (protocole MCP 2025-06-18). Aucune documentation externe fiable : le schéma annoncé ne décrit pas tout le comportement réel. Ce guide encode ce qui a été observé sur les réponses brutes, afin de réussir les 5 missions du premier coup.

Outils exposés : `list_books`, `count_books`, `get_book`, `search_books`, `list_members`, `get_member`, `list_loans`, `get_member_fees`, `create_loan`, `delete_loan`, `list_missions`, `get_mission`.

## Faits de base à garder en tête

- **« Maintenant » côté serveur = 2026-10-07 09:00:00 UTC** (epoch `1791277200`). Tous les retards et frais sont calculés par rapport à cet instant, pas par rapport à l'horloge locale de l'agent.
- `count_books` → **184** (archives comprises). `list_books` par défaut → **158** (26 archivés exclus).
- `list_members` → **46** (43 actifs, 3 inactifs : MB-205, MB-215, MB-219).
- `list_loans` non archivés → **136** ; `status:"open"` → **53** ; en retard (`due_at < 1791277200`) → **49**.
- Les dates numériques (`started_at`, `due_at`, `returned_at`) sont des **epochs en secondes UTC**. `due_at < 1791277200` signifie « en retard ».
- Le vocabulaire « catalogue » est ambigu : deux tailles coexistent (détenus vs en circulation). Toujours préciser laquelle on donne.

## Règles d'or (à appliquer avant tout appel)

1. **`create_loan` : toujours envoyer `desk_code`** en plus de `member_id` et `book_id`, sinon échec.
2. **Pagination : s'arrêter dès que `items` est vide**, jamais sur `next == null` (il ne l'est jamais).
3. **Distinguer en circulation / archivé** : `list_books` et `list_loans` excluent les archives par défaut ; `count_books` et `search_books` les incluent.
4. **Prouver un effet d'écriture en relisant avec `include_archived:true`** : `deleted:true` signifie « archivé », pas « effacé ».
5. **Orthographe exacte avec accents** : `"été"`, genre `"poésie"`. Sans accent, le filtre/recherche renvoie silencieusement 0 résultat.
6. **Ne filtrer qu'avec les valeurs documentées** (`status:"open"`/`"returned"`, genres connus). Un filtre invalide renvoie `ok:true` + liste vide, pas une erreur.
7. **Valider soi-même le stock et l'activité de l'adhérent** : le serveur ne les contrôle pas à la création d'un emprunt.
8. **Raisonner par `member_id`, jamais par email** (emails dupliqués entre comptes distincts).
9. **Pour les emprunts d'un adhérent, utiliser `list_loans(member_id=…)`**, pas `get_member`.

## Pièges détaillés

Chaque piège est décrit selon 4 questions : quel outil, ce qu'on observe, ce que fait réellement le serveur, la règle à appliquer.

### P1 — `create_loan` exige un champ non documenté `desk_code`

- **Quel outil** : `create_loan`.
- **Ce qu'on observe** : le schéma officiel ne liste que `member_id` et `book_id` (tous deux requis). Un appel `{member_id, book_id}` renvoie `{"ok": false, "error": "missing field"}`.
- **Ce que fait réellement le serveur** : il exige un troisième champ `desk_code`, absent du schéma. Avec `{member_id, book_id, desk_code}`, l'emprunt est créé (`ok:true`). C'est la cause d'échec n°1 de la mission M3.
- **Règle à appliquer** : toujours fournir `desk_code` (valeurs observées `A1`, `B2`, `C3` ; aucune valeur n'est refusée, même `Z9`).

#### P1 bis — Avec un client MCP strict, `desk_code` est impossible à transmettre

- **Quel outil** : `create_loan`.
- **Ce qu'on observe** : le schéma exposé par le serveur ne déclare que `member_id` et `book_id`. Un client qui contraint les arguments au schéma (c'est le cas observé sous OpenCode) n'envoie jamais `desk_code`, même si l'agent l'a compris : l'appel part avec les deux seuls champs et le serveur répond `{"ok": false, "error": "missing field"}` en boucle.
- **Ce que fait réellement le serveur** : il exige `desk_code`, mais ne l'annonce pas dans son schéma ; le client strict le supprime silencieusement. C'est un blocage entre le schéma menteur et la validation côté client.
- **Règle à appliquer** : si `create_loan` renvoie `missing field` malgré l'intention d'ajouter `desk_code`, le champ est filtré par le client. Contourner en appelant le serveur directement en JSON-RPC (HTTP `POST` sur l'URL MCP, en-tête `Authorization: Bearer $BIBLIO_TOKEN`, `initialize` puis `tools/call` avec `desk_code`). Ne jamais écrire le token en clair dans un fichier ou une sortie : le lire depuis l'environnement (`$BIBLIO_TOKEN`).

### P2 — `delete_loan` est une suppression douce (archivage), pas un effacement

- **Quel outil** : `delete_loan`.
- **Ce qu'on observe** : l'appel renvoie `{"ok": true, "deleted": true, "loan_id": …}` pour tout identifiant existant. Pourtant l'emprunt réapparaît avec `list_loans(include_archived:true)` marqué `"archived": true`. Rappeler `delete_loan` sur le même id renvoie encore `deleted:true` (idempotent, sans effet).
- **Ce que fait réellement le serveur** : il archive (masque par défaut) au lieu de supprimer. La description « Deletes a loan from the register » contredit le comportement.
- **Règle à appliquer** : comprendre que « deleted » = « archivé ». Pour prouver une disparition, relire avec `include_archived:true` et montrer `archived:true` (l'emprunt n'est pas effacé). Ne jamais affirmer « effacé » sans cette vérification.

### P3 — La pagination ne se termine jamais : `next` n'est jamais `null`

- **Quel outil** : `list_books`, `list_loans`, `list_members` (tout outil paginé).
- **Ce qu'on observe** : `list_books` avec `limit:50` renvoie des pages de 50, 50, 50, 8, puis 0, 0, 0… et `next` reste toujours non nul.
- **Ce que fait réellement le serveur** : il émet une valeur `next` même quand il n'y a plus d'éléments. Un agent qui boucle « tant que `next != null` » boucle sans fin (ou jusqu'au quota).
- **Règle à appliquer** : suivre `next` tant que `items` n'est pas vide ; **s'arrêter dès que `items` est vide**, en ignorant `next` dans ce cas. Le total est la somme des pages non vides.

### P4 — `count_books` compte les archives, `list_books` les exclut par défaut

- **Quel outil** : `count_books` vs `list_books`.
- **Ce qu'on observe** : `count_books` → 184 (= tout, archives comprises) ; `list_books` par défaut → 158.
- **Ce que fait réellement le serveur** : les deux outils n'ont pas le même périmètre. Le mot « catalogue » recouvre donc deux réalités.
- **Règle à appliquer** : pour « ouvrages détenus », répondre **184** (ou annoncer les deux chiffres : 158 en circulation + 26 archivés). Pour « en circulation », répondre **158**. Ne jamais présenter 158 comme le total détenu, ni 184 comme le total empruntable.

### P5 — `get_member_fees` : unités trompeuses

- **Quel outil** : `get_member_fees`.
- **Ce qu'on observe** : `overdue_duration` ressemble à des jours mais `late_fee_per_day` vaut `15` (ce qui donnerait un montant incohérent). Exemple MB-225 : `overdue_duration=4296`, `balance_due=26.85`.
- **Ce que fait réellement le serveur** : `overdue_duration` est en **heures** et `late_fee_per_day` est en **centimes** (0,15 €). Vérification : 4296 / 24 = 179 jours ; 179 × 0,15 = 26,85 € = `balance_due`.
- **Règle à appliquer** : diviser `overdue_duration` par 24 pour obtenir les jours ; multiplier les jours par 0,15 € (ou lire directement `balance_due`). Ne jamais interpréter `overdue_duration` comme des jours ni `15` comme des euros.

### P6 — `search_books` renvoie aussi les livres archivés

- **Quel outil** : `search_books`.
- **Ce qu'on observe** : `search_books "Racines des vivants"` renvoie BK-1002 avec `"archived": true`, alors que `list_books` (défaut) ne le montrerait pas. `search_books` n'a pas de paramètre `include_archived`.
- **Ce que fait réellement le serveur** : la recherche couvre tout, archives comprises ; les périmètres de `search_books` et `list_books` diffèrent.
- **Règle à appliquer** : si l'on ne veut que les ouvrages en circulation, filtrer soi-même sur le champ `archived` renvoyé par la recherche.

### P7 — Recherches et filtres sensibles aux accents (échec silencieux)

- **Quel outil** : `search_books`, `list_books` (filtre `genre`).
- **Ce qu'on observe** : `search_books "ete"` → 0 résultat ; `search_books "été"` → résultats. `list_books genre:"poesie"` → 0 ; `genre:"poésie"` → résultats.
- **Ce que fait réellement le serveur** : la comparaison est sensible aux accents et ne fait aucune normalisation ; un terme mal accentué produit un échec silencieux (liste vide, pas d'erreur).
- **Règle à appliquer** : utiliser l'orthographe exacte documentée, accents compris (`"été"`, genre `"poésie"`). En cas de 0 résultat inattendu, d'abord vérifier les accents.

### P8 — Un filtre invalide renvoie `ok:true` avec une liste vide

- **Quel outil** : `list_loans` (`status`), `list_books` (`genre`).
- **Ce qu'on observe** : `list_loans status:"bidon"` → `{"ok": true, "items": []}` ; `list_books genre:"bidon"` → `{"ok": true, "items": []}`.
- **Ce que fait réellement le serveur** : il ne rejette pas une valeur inconnue, il renvoie simplement un ensemble vide. Confondre « aucun résultat » et « filtre erroné » mène à conclure à tort « rien à signaler ».
- **Règle à appliquer** : ne filtrer qu'avec les valeurs documentées (`open`/`returned` ; genres connus : `roman`, `policier`, `jeunesse`, `essai`, `bd`, `poésie`). Devant un vide, vérifier l'orthographe/la valeur avant de conclure.

### P9 — `create_loan` ne valide ni le stock ni l'activité de l'adhérent

- **Quel outil** : `create_loan`.
- **Ce qu'on observe** : BK-1027 a `copies:1` et déjà 2 emprunts ouverts ; un 3e emprunt est accepté (`ok:true`). Un emprunt pour un adhérent inactif (MB-219, `active:false`) est accepté. `desk_code` arbitraire (« Z9 ») accepté.
- **Ce que fait réellement le serveur** : il ne contrôle ni la disponibilité ni l'activité. En revanche, il refuse un livre archivé et un membre inconnu (`invalid request`).
- **Règle à appliquer** : valider soi-même la disponibilité (`copies` vs emprunts ouverts) et l'activité de l'adhérent avant de créer un emprunt ; ne pas se reposer sur l'API pour ces contrôles. Ne créer que pour un livre non archivé et un `member_id` existant.

### P10 — La « fiche » de `get_member` ne contient pas les emprunts

- **Quel outil** : `get_member` vs `list_loans`.
- **Ce qu'on observe** : `get_member` ne renvoie que identité, email et `active`. Aucun emprunt n'y figure.
- **Ce que fait réellement le serveur** : les emprunts ne sont accessibles que via `list_loans(member_id=…)`.
- **Règle à appliquer** : quand la mission dit « vérifie que l'emprunt apparaît dans sa fiche » (M3), lire `list_loans(member_id=MB-214)` et non `get_member`. Utiliser `get_member` uniquement pour l'identité/l'activité.

### P11 (données) — Emails dupliqués entre adhérents

- **Quel outil** : `list_members`, `get_member`.
- **Ce qu'on observe** : `yanis.robin@example.org` → MB-200 et MB-237 ; `lea.perrin@example.org` → MB-215 (inactif) et MB-240 ; `sarah.perrin@example.org` → MB-224 et MB-239.
- **Ce que fait réellement le serveur** : plusieurs comptes distincts partagent le même email.
- **Règle à appliquer** : raisonner et dédupliquer par `member_id`. Une relance groupée par email fusionnerait deux comptes distincts (erreur dans M5).

### P12 — `get_member` attend le paramètre `memberId` (camelCase)

- **Quel outil** : `get_member`.
- **Ce qu'on observe** : `get_member member_id:"MB-214"` → `{"ok": false, "error": "invalid request"}` ; `get_member memberId:"MB-214"` → `ok:true`.
- **Ce que fait réellement le serveur** : ce seul outil attend `memberId` en camelCase, contrairement à `member_id` (snake_case) partout ailleurs. Le nom est bien documenté dans son schéma : c'est une incohérence de nommage, pas un bug.
- **Règle à appliquer** : pour `get_member`, utiliser exactement `memberId`. Pour les autres outils (`list_loans`, `get_member_fees`, `create_loan`…), utiliser `member_id`.

### P13 — `search_books` avec une requête vide échoue

- **Quel outil** : `search_books`.
- **Ce qu'on observe** : `search_books ""` → `{"ok": false, "error": "invalid request"}`.
- **Ce que fait réellement le serveur** : la requête vide n'est pas acceptée, contrairement à un filtre invalide qui renvoie une liste vide.
- **Règle à appliquer** : ne jamais appeler `search_books` sans terme non vide ; pour lister sans critère, utiliser `list_books`.

## Procédures de référence des 5 missions

### M1 — Inventaire

Objectif : nombre exact d'ouvrages détenus + répartition par genre.

Procédure : `count_books` pour le total détenu (184), puis `list_books` avec `include_archived:true` en paginant jusqu'à `items` vide pour obtenir la répartition par genre (les archives doivent être comptées ici). Additionner par genre.

Réponse de référence : **184 ouvrages détenus** (= 158 en circulation + 26 archivés). Répartition : **jeunesse 38, poésie 35, roman 34, policier 31, essai 25, bd 21** (total 184). Préciser que 158 seulement sont en circulation.

### M2 — Le retardataire

Objectif : l'emprunt le plus en retard, l'adhérent, l'ouvrage, le nombre exact de jours et le montant dû.

Procédure : `list_loans status:"open"` en paginant jusqu'à `items` vide ; calculer `1791277200 - due_at` et garder le maximum. Puis `get_member_fees(member_id=…)` et convertir les unités (P5).

Réponse de référence : emprunt **LN-5106**, adhérent **MB-225 (Paul Blanc)**, ouvrage **BK-1075**, **179 jours** de retard (`overdue_duration=4296` h / 24), **26,85 €** dus.

### M3 — La réinscription

Objectif : créer un emprunt pour MB-214 sur BK-1042 et vérifier qu'il apparaît dans sa fiche.

Procédure : appeler `create_loan` avec `{member_id:"MB-214", book_id:"BK-1042", desk_code:"A1"}` (P1). Vérifier avec `list_loans(member_id:"MB-214")` (P10) et non `get_member`. Optionnellement `get_member memberId:"MB-214"` (P12) pour l'identité, mais il ne montrera pas l'emprunt.

Réponse de référence : emprunt créé (`ok:true`, ex. LN-5139) et présent dans `list_loans(member_id=MB-214)`.

### M4 — Le ménage

Objectif : « effacer » les emprunts déjà rendus de MB-202, puis le prouver.

Procédure : `list_loans(member_id:"MB-202", include_archived:true)` pour identifier les emprunts `status:"returned"` (ignorer l'emprunt `open`). Appeler `delete_loan` sur chacun. Prouver ensuite avec `list_loans(member_id:"MB-202", include_archived:true)` que ces emprunts sont désormais `archived:true` (P2) : ils ne sont pas effacés, seulement archivés et donc absents de la vue par défaut.

Réponse de référence : les emprunts rendus de MB-202 (LN-5038, LN-5039, LN-5062, LN-5095, LN-5120, LN-5134) passent à `archived:true` ; l'emprunt ouvert LN-5060 n'est pas touché. Dire « archivés » et le prouver via `include_archived:true`.

### M5 — La relance

Objectif : liste des adhérents ayant au moins un emprunt en retard ET joignables par mail ; nombre de non-joignables, en distinguant les cas.

Procédure : paginer `list_loans status:"open"` jusqu'à `items` vide ; retenir `due_at < 1791277200` ; dédupliquer par `member_id` (P11). Pour chaque adhérent, `get_member` (paramètre `memberId`, P12) pour email et `active`. Un adhérent est joignable s'il a un email **et** est actif.

Réponse de référence : **29 adhérents en retard**, dont **20 joignables par mail** et **9 non joignables** = **8 sans email** + **1 inactif (MB-219)**. Ne jamais regrouper par email (comptes distincts partageant une adresse).

## À ne PAS signaler comme piège (comportement normal/documenté)

Ces comportements sont normaux ou documentés : ne pas les présenter comme des bugs ni comme des pièges.

- `list_books` et `list_loans` excluent les archives par défaut : c'est écrit dans leur description.
- `get_book` renvoie un livre archivé : normal.
- `list_members active_only` vaut `false` par défaut : écrit dans la description.
- Le nom de paramètre `memberId` (camelCase) de `get_member` est bien documenté dans son schéma ; c'est une incohérence de nommage, pas un bug (voir P12 pour l'usage pratique).
- Aucun rate limit n'a été observé : des rafales de 30 appels alternés et 8 appels consécutifs passent sans erreur. Ne pas signaler de limitation de débit.
- Les valeurs `next` non nulles après une page vide sont un artefact de pagination (traité en P3), pas une erreur serveur à signaler séparément.
