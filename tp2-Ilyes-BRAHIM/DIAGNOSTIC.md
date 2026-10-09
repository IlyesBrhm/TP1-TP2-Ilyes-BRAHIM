# DIAGNOSTIC — TP2 « Le repo malade » (salles-api)

Ce document recense ce qui est cassé dans le dépôt, la preuve de chaque problème
(commande lancée + sortie observée), la brique du cours concernée, et la correction
appliquée. Il se termine par ce qui a été **volontairement non corrigé**.

Branche de travail : `fix/harness-repair` (AGENTS.md interdit de commiter sur `main`).

> Note sur les preuves : toutes les preuves sont dans `captures/`, au format **PNG**
> (rendu de la sortie terminal de chaque commande, accents et couleurs compris). La
> machine n'ayant pas d'environnement graphique, ce sont des rendus de terminal et non
> des captures d'écran au sens strict. Voir `captures/README.md`.

---

## 1. Synthèse

| # | Brique | Problème | Fichier(s) | Statut |
|---|---|---|---|---|
| 1 | rules | AGENTS.md annonce `npm test` et `npm run build`, scripts inexistants | `AGENTS.md`, `package.json` | corrigé |
| 2 | rules | AGENTS.md annonce une convention `Result` jamais appliquée | `AGENTS.md` | corrigé |
| 3 | rules | AGENTS.md §1 (JSDoc partout) contredit `src/lib/AGENTS.md` (pas de JSDoc) | `AGENTS.md` | corrigé |
| 4 | rules | `src/lib/AGENTS.md` exige un `export default` ; modules non conformes | `src/lib/*.ts` | partiel |
| 5 | MCP | 6 serveurs déclarés, la plupart injoignables/inutiles | `opencode.json`, `.env` | corrigé |
| 6 | commands | `/ship` pousse sans rejouer les checks ni relire, et commite sur `main` | `.opencode/command/ship.md` | corrigé |
| 7 | skills | aucun skill packagé | `.opencode/` | non corrigé (défendable) |
| 8 | subagents | README annonce 6 subagents ; `planner` est `mode: primary` (5 réels) | `README.md`, `planner.md` | corrigé |
| 9 | subagents | `tester` absent de l'équipe et de la boucle de l'architect → jamais appelé | `architect.md` | corrigé |
| 10 | subagents | IDs de modèles inexistants → **tous** les subagents échouent | `*.md`, `opencode.json` | corrigé |
| 11 | subagents | règle de délégation inversée dans le prompt de l'architect | `architect.md` | corrigé |
| 12 | droits | `architect` peut écrire du code alors que son rôle l'interdit | `architect.md` | corrigé |
| 13 | droits | `explorer` peut écrire n'importe où | `explorer.md` | corrigé |
| 14 | droits | `reviewer` écrit du code alors que `dev` se dit « seul à écrire » | `reviewer.md` | non corrigé (choix) |
| 15 | hooks | pre-commit husky présent mais **jamais installé/branché** | `.husky/`, `package.json` | corrigé |
| 16 | hooks | plugin post-écriture appelle `bash` → échoue (WSL absent) | `.opencode/plugin/checks.js` | corrigé |
| 17 | lint | config eslint avec `rules: {}` → lint qui ne vérifie rien | `eslint.config.js` | corrigé |
| 18 | types | `strict: false` + `@ts-nocheck` | `tsconfig.json`, `price.ts` | corrigé |
| 19 | tests | `bookings.test.ts` / `price.test.ts` jamais exécutés (mauvais suffixe) | `vitest.config.ts` | corrigé |
| 20 | tests | `overlaps` utilise des bornes fermées → créneaux mitoyens « en conflit » | `src/lib/overlap.ts` | corrigé |
| 21 | tests | `WEEKEND_SURCHARGE = "20"` (string) → concaténation au lieu d'addition | `src/lib/price.ts` | corrigé |
| 22 | tests | `store.spec.ts` teste un double, pas le vrai store | `test/store.spec.ts` | corrigé |
| 23 | tests | 3 `it.skip` non justifiés sur des cas limites | `test/overlap.spec.ts` | corrigé |
| 24 | CI/Git | étape de tests commentée dans la CI ; lint vide = CI verte à vide | `.github/workflows/ci.yml` | corrigé |

---

## 2. Détail des problèmes

### Brique « rules »

**1. Les commandes annoncées n'existent pas.**
- Symptôme : `AGENTS.md` documente `npm test` (« à lancer avant tout commit ») et
  `npm run build` (« compile dans dist/ »).
- Preuve :
  ```
  $ npm test        -> npm error Missing script: "test"
  $ npm run build   -> npm error Missing script: "build"
  ```
- Cause : `package.json` ne définit que `test:unit`, `lint`, `typecheck`, `start`, `dev`.
- Correction : ajout de `"test"` (alias vitest) et `"build"` (`tsc -p tsconfig.build.json`,
  nouveau `tsconfig.build.json`), donc la doc redevient vraie.

**2. La convention d'erreurs est fausse.**
- Symptôme : `AGENTS.md` §2 affirme « Les erreurs remontent en `Result`, jamais en
  `throw`… depuis la refonte de mars ».
- Preuve : `grep -r "Result" src/` → aucun type `Result` dans le dépôt ; à l'inverse
  `src/lib/validate.ts:10,18,27` lèvent `ValidationError`, `src/routes/bookings.ts:58`
  contient un `try/catch`.
- Cause : la « refonte » annoncée n'a pas eu lieu ; la doc décrit un code qui n'existe pas.
- Correction : la doc décrit maintenant le code réel (validation par `ValidationError`
  typée, convertie en 400 par la route). Le refactor vers `Result` n'a pas été fait : il
  toucherait `validate.ts`, `bookings.ts` et la sémantique HTTP pour un gain de style, et
  le sujet demande de réparer ce qui est cassé, pas de réécrire l'architecture.

**3. Deux règles JSDoc contradictoires.**
- `AGENTS.md` §1 : « Toute fonction exportee porte une JSDoc ».
- `src/lib/AGENTS.md` : « Pas de JSDoc ici ».
- Correction : §1 est désormais explicitement limité (« sauf dans `src/lib/` »), ce qui
  lève la contradiction sans casser la convention locale.

**4. `export default` obligatoire non respecté (partiel).**
- `src/lib/AGENTS.md` impose un `export default` par module (raison invoquée : scripts de
  facturation chargeant par chemin). `price.ts` et `overlap.ts` n'en avaient pas.
- Correction : ajout de `export default priceFor` et `export default overlaps`.
- Non corrigé : `validate.ts` n'a pas de fonction principale unique (classe + 3 helpers) ;
  ajouter un default serait arbitraire. À trancher avec l'équipe.

### Brique « MCP »

**5. Six serveurs MCP déclarés, tous `enabled: true`, la plupart inutilisables.**
- `salles-db` : URL interne `https://mcp.internal.salles.lan/db` + `${SALLES_MCP_TOKEN}`.
  Preuve : `.env` ne contient **pas** `SALLES_MCP_TOKEN` (il contient `SALLES_DB_URL`,
  `SESSION_SECRET`, `STRIPE_SECRET_KEY`). De plus le store est en mémoire (INFRA-140).
- `notion`, `slack`, `sentry` : aucun jeton correspondant dans l'environnement.
- `playwright` : automatisation navigateur, sans objet pour une API HTTP.
- `github` : utile pour le dépôt (PR), conservé.
- Correction : `opencode.json` ne garde que `github`. Un MCP injoignable ralentit le
  démarrage et pollue le contexte de l'agent pour rien.

### Brique « skills et commands »

**6. La commande `/ship` est dangereuse.**
- Symptôme : elle faisait `git add -A && git commit && git push`, « sans poser de
  question », en **sautant les checks** (« le hook post-ecriture s'en est deja occupe »)
  et la relecture, et sans contrainte de branche — alors qu'`AGENTS.md` interdit de
  commiter sur `main`.
- Cause : `.opencode/command/ship.md`.
- Correction : `/ship` rejoue désormais lint + typecheck + tests, crée une branche si l'on
  est sur `main`, puis pousse la branche et ouvre une PR (c'est la CI qui valide).

**7. Aucun skill.** Non corrigé : aucun workflow répétitif du dépôt ne justifie un skill
packagé (voir §3).

### Brique « subagents »

**8. Le compte annoncé est faux.**
- `README.md` : « un agent principal `architect` et six subagents specialises ».
- Réalité : `planner` était déclaré `mode: primary` → seulement **5** subagents
  (`dev`, `explorer`, `finder`, `reviewer`, `tester`), et `planner` n'était pas joignable
  comme subagent alors que l'architect est censé lui déléguer la planification.
- Correction : `planner` passe en `mode: subagent`. Le dépôt a alors bien 1 primary + 6
  subagents, comme le README l'annonce.

**9. `tester` n'était jamais appelé.**
- Le tableau d'équipe et la boucle de `architect.md` listaient `finder`, `explorer`,
  `planner`, `dev`, `reviewer` — **pas `tester`**. Confirmé par la trace du run « avant » :
  seuls `explorer` et `reviewer` sont invoqués.
- Correction : `tester` ajouté au tableau et à l'étape de vérification.

**10. Les modèles des agents n'existent pas → tous les subagents échouent.**
- Preuve (trace du run « avant », `captures/avant/chain-errors.png`) :
  ```
  ERROR ProviderModelNotFoundError: Model not found: opencode/deepseek-v4-flash
  ERROR ProviderModelNotFoundError: Model not found: opencode/deepseek-v4-pro
  ```
- `opencode models` ne liste aucun de ces deux IDs ; les disponibles sont
  `opencode/deepseek-v4.1-flash`, `opencode/muse-spark-1.3-contributor-free`,
  `opencode/claude-haiku-5-5`, `opencode/exo-free`, `opencode/deepseek-v4-flash-vision-exp`.
- Conséquence : chaque `task` de l'architect vers un subagent échoue ; l'architect
  (qui avait le droit d'écrire) faisait alors le travail lui-même — la chaîne entière
  était court-circuitée **silencieusement**.
- Correction : IDs repointés vers les modèles réellement disponibles (voir §3 pour la
  réserve d'environnement).

**11. Règle de délégation inversée dans le prompt de l'architect.**
- `architect.md` disait : « If a question can be answered by a subagent, it can also be
  answered by you. » — l'inverse du principe de délégation, et exactement le comportement
  observé « avant ».
- Correction : « …it should be answered by the subagent, not by you. »

### Brique « droits »

**12. `architect` pouvait écrire du code.**
- Sa description dit « Never writes code », mais ses permissions contenaient
  `edit: allow` et `bash: "*": allow` (commit `865177b` : « architect: unblock, trop de
  refus de permission en session »).
- Preuve : dans le run « avant », l'architect a créé/édité `src/lib/availability.ts`,
  `src/routes/rooms.ts`, les deux tests — il a écrit le code.
- Correction : `edit` refusé (via `"*": deny`), `bash` restreint à la lecture git, au
  commit/push (nécessaire à `/ship`) et à `npm run`.

**13. `explorer` pouvait écrire n'importe où.**
- `edit: allow` alors que son prompt dit qu'il ne fait que lire et dépose ses notes.
- Correction : `edit` limité à `.opencode/plans/*.md`.

### Brique « hooks »

**14. Le pre-commit husky n'a jamais tourné.**
- Symptômes : `.husky/pre-commit` existe et sourçait `.husky/_/husky.sh`, mais
  `husky` n'est pas une dépendance, il n'y a pas de script `prepare`, `.husky/_/` n'existe
  pas, et `git config core.hooksPath` était vide.
- Preuve :
  ```
  $ git config core.hooksPath      -> (vide)
  $ Test-Path node_modules/.bin/husky* -> False
  ```
  donc aucun hook n'était branché : `npm test` n'était pas lancé avant commit.
- Correction : hook rendu autonome (plus de dépendance à `husky.sh`) + script
  `"prepare": "git config core.hooksPath .husky"` dans `package.json` (pas de nouvelle
  dépendance). Vérifié par un vrai `git commit` : le hook exécute lint, typecheck et
  tests (`captures/04-hook-precommit.png`).

**15. Le plugin de checks post-écriture ne pouvait pas tourner.**
- Le plugin `.opencode/plugin/checks.js` lance `bash scripts/checks.sh`. Sur cette
  machine, `bash` est le lanceur WSL sans distribution :
  ```
  $ bash scripts/checks.sh
  Le sous-système Windows pour Linux n'a aucune distribution installée.
  exit=1
  ```
- Le commentaire de `scripts/checks.sh` référence en outre un mécanisme obsolète
  (`experimental.hook.file_edited`) absent d'`opencode.json` ; en réalité le plugin est
  chargé par le dossier `.opencode/plugin/` (vérifié : le hook `tool.execute.after` se
  déclenche bien sur `edit`/`write`, avec `input.args.filePath` et `output.output`).
- Correction : le plugin appelle directement les scripts npm (`typecheck`, `lint`,
  `test`) via le shell `$` d'opencode, sans dépendre de `bash`. Le filet redevient
  portable.
- Non corrigé volontairement : `scripts/checks.sh` renvoie toujours `exit 0`. C'est un
  choix documenté (INFRA-231 : ne pas interrompre l'agent). Ce n'est pas un défaut — le
  vrai défaut était qu'il n'était jamais invoqué.

### Brique « lint et types »

**16. Le lint ne vérifiait rien.**
- `eslint.config.js` : parser TypeScript branché, mais `rules: {}`.
- Preuve : `npm run lint` passe sur n'importe quoi. Test : ajout d'un fichier
  `src/__lintprobe.ts` avec `const unused: any = 1` → **avant**, lint vert ; **après**
  correction, lint rouge :
  ```
  error 'unused' is assigned a value but never used  @typescript-eslint/no-unused-vars
  error Unexpected any. Specify a different type      @typescript-eslint/no-explicit-any
  ```
  (`captures/03-lint-actif.png`).
- Correction : `tseslint.configs.recommended` + `ignores`.

**17. Le typecheck ne vérifiait presque rien.**
- `tsconfig.json` : `strict: false`, `noImplicitAny: false`, `strictNullChecks: false` ;
  et `src/lib/price.ts` portait `// @ts-nocheck` (fichier entièrement exclu du typage).
- Correction : `strict: true`, suppression de `@ts-nocheck`. Le code passe (les erreurs
  latentes réelles sont dans les tests, cf. plus bas).

### Brique « tests »

**18. Deux fichiers de tests ne s'exécutaient jamais.**
- `vitest.config.ts` inclut `test/**/*.spec.ts`, mais `test/bookings.test.ts` et
  `test/price.test.ts` portaient le suffixe `.test.ts`.
- Preuve : `npm run test:unit` ne découvrait que 2 fichiers (overlap, store), 5 tests.
- Correction : renommage en `.spec.ts` (convention documentée dans `vitest.config.ts`).
  **C'est cette correction qui a révélé les bugs 20 et 21.**

**19. `overlaps` traite les bornes comme fermées.**
- `src/lib/overlap.ts` : `return a1 <= b2 && b1 <= a2`, alors que le commentaire du fichier
  annonce `[debut, fin[`. Deux créneaux mitoyens (09–10 et 10–11) étaient vus en conflit.
- Preuve (après renommage des tests) :
  ```
  test/bookings.spec.ts > accepte une reservation qui commence quand la precedente finit
  AssertionError: expected 409 to be 201
  ```
- Correction : `a1 < b2 && b1 < a2`, conforme au commentaire et aux cas mitoyens.

**20. Le prix week-end concatène au lieu d'additionner.**
- `src/lib/price.ts` : `const WEEKEND_SURCHARGE = "20";` (chaîne) puis
  `base + WEEKEND_SURCHARGE`.
- Preuve (après renommage des tests) :
  ```
  test/price.spec.ts > ajoute la majoration de week-end
  AssertionError: expected '5020' to be 70
  ```
- Correction : `const WEEKEND_SURCHARGE = 20;`.

**21. `store.spec.ts` testait un double, pas le store.**
- Le test définissait `storeDouble` (un mock en dur) et assertait dessus : il resterait
  vert même si le vrai store était cassé.
- Correction : les tests importent et exercent `rooms`, `findRoom`, `bookingsForRoom`
  réels.

**22. Trois `it.skip` non justifiés.**
- `test/overlap.spec.ts` skippait « bout à bout », « creneau inclus », « creneaux
  identiques » sans raison, dont deux avec un corps `expect(true).toBe(true)`.
- Correction : réactivés avec de vraies assertions. Le 4e skip (export de l'ancien
  système) est conservé : il est **documenté** (fixture `legacy-bookings.json` jamais
  versée, INFRA-198) et ne peut pas être réactivé sans elle.

### Brique « CI et Git »

**23. La CI ne testait rien.**
- `.github/workflows/ci.yml` : l'étape `npm run test:unit` était commentée
  (« TODO remettre, ca bloquait les merges ») ; il ne restait que `npm run lint`, qui ne
  vérifiait rien (bug 16). La CI verte était donc vide de sens.
- Correction : lint + typecheck + build + test sur chaque push `main` et chaque PR.

---

## 3. Ce qui n'est pas corrigé, et pourquoi

- **Le refactor `Result`** (rules #2) : non fait, on a corrigé la doc. Voir §2.2.
- **`reviewer` qui écrit du code** (droits #14) : le prompt de `reviewer.md` fait
  explicitement le choix de corriger directement (« Fix what you find », « that is pure
  waste »), alors que `dev.md` se dit « the only agent allowed to change code ». La
  contradiction est réelle, mais le comportement du reviewer est documenté et défendu ;
  je ne l'ai pas changé pour ne pas contredire un choix délibéré. À trancher.
- **Les IDs de modèles** (#10) : les IDs d'origine (`opencode/deepseek-v4-pro`,
  `opencode/deepseek-v4-flash`) n'existent pas sur le provider utilisé ici, prouvé par
  `ProviderModelNotFoundError`. Je les ai repointés vers des modèles disponibles sur
  **ce** provider. Si l'environnement de notation expose d'autres IDs, il faut adapter
  `opencode.json` et les frontmatters. C'est le seul correctif dépendant de
  l'environnement.
- **`scripts/checks.sh` (`exit 0`)** : choix documenté (INFRA-231), conservé.
- **Le 4e `it.skip`** (`legacy-bookings.json`) : skip assumé et documenté (INFRA-198).
- **`src/lib/AGENTS.md` (pas de JSDoc)** : règle de chemin délibérée, conservée.
- **`src/store.ts`** : jamais touché (AGENTS.md + INFRA-140).
- **`.env`** : les secrets sont des fixtures pédagogiques explicitement annotées
  (« JEU DE DONNEES PEDAGOGIQUE »), rien à corriger.
- **Aucun skill** (#7) : absence défendable, aucun workflow répétitif à packager.
- **Le `noEmit: true` du `tsconfig.json` de base** : normal pour un typecheck ; le build
  utilise `tsconfig.build.json`.

---

## 4. Exercice 1 — avant / après

Tâche relancée à l'identique : « Ajoute un endpoint GET /rooms/:id/availability?date=YYYY-MM-DD
qui renvoie les creneaux libres d'une salle sur la journee demandee, avec ses tests. »

### Avant (dépôt malade)

- Agents réellement utilisés (trace OpenCode) : `architect` + 2 appels `explorer` + 1
  `reviewer`, **tous deux échouant** sur `ProviderModelNotFoundError`. `finder`,
  `planner`, `dev`, `tester` : **jamais appelés**.
- L'`architect` a écrit lui-même tout le code (droit `edit` ouvert), sans plan sur disque,
  sans relecture effective, sans tester. Session coupée après >5 min sans fin.
- Preuves : `captures/avant/git-status.png`, `captures/avant/diff-avant.png`,
  `captures/avant/chain-errors.png`.

### Après (dépôt réparé)

- Agents utilisés : `architect` → `finder` (4) + `explorer` (8) + `planner` (7) →
  `dev` (34, en 4 étapes) → `reviewer` (10) + `tester` (5). **Aucune erreur de modèle.**
- Un plan est écrit sur disque : `.opencode/plans/availability.md` ; des notes
  d'exploration : `.opencode/plans/rooms-bookings-current-notes.md`.
- Le `dev` a produit `src/lib/availability.ts`, le endpoint dans `src/routes/rooms.ts`,
  et les deux fichiers de tests. Filet vert : `lint`, `typecheck`, `build`, **38 tests
  passent** (6 fichiers).
- Preuves : `captures/06-apres-chain.png`, `captures/07-apres-tests.png`.

| | Avant | Après |
|---|---|---|
| Subagents réellement exécutés | 0 (2 échecs modèle) | 5 |
| Plan sur disque | non | oui |
| Relecture effective | non | oui (`reviewer`) |
| Test utilisateur | non | oui (`tester`) |
| Qui écrit le code | `architect` | `dev` |
| Fin de session | timeout, non concluante | tâche implémentée, suite verte |

Réserve honnête : `captures/avant/` était présent dans le dépôt pendant le run « après »,
et le `planner` s'en est servi comme contrat (il le signale lui-même dans
`.opencode/plans/availability.md`, hypothèses). L'implémentation « après » ressemble donc
beaucoup à celle du run « avant » : la démonstration porte sur le **comportement de la
chaîne** (délégation, plan, vérification), pas sur une différence de code.
