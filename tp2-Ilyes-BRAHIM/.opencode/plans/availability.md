# Ajouter GET /rooms/:id/availability?date=YYYY-MM-DD et ses tests

## Goal
`GET /rooms/:id/availability?date=YYYY-MM-DD` renvoie les créneaux libres d'une salle sur la journée demandée, `npm test`, `npm run lint` et `npm run build` sont verts.

## Non-goals
- Ne pas toucher à `src/store.ts` (interdit : AGENTS.md, INFRA-140) — lecture seule via `findRoom` / `bookingsForRoom`.
- Pas d'horaires d'ouverture, pas de récurrence, pas de pagination/filtrage supplémentaire.
- Pas de nouvelle dépendance.
- Pas de modification de `POST /bookings`, `GET /rooms`, `GET /rooms/:id`, `src/lib/overlap.ts`, `src/lib/price.ts`, `src/lib/validate.ts`.

## Assumptions and open questions
- assumption: Format de réponse tranché d'après `captures/avant/rooms-availability.spec.ts:23-30` : `{ roomId: string, date: "YYYY-MM-DD", freeSlots: [{ startsAt: ISO, endsAt: ISO }] }`. Journée = `[dateT00:00:00Z, lendemainT00:00:00Z[` UTC. Bornes ISO 8601 UTC `string` à la seconde (`YYYY-MM-DDTHH:mm:ssZ`, sans millisecondes), jamais de `Date` dans le JSON (convention AGENTS.md §3).
- assumption: `captures/avant/availability.ts` + `captures/avant/*.spec.ts` sont des specs/captures à reproduire, pas du code courant (`src/lib/availability.ts` absent vérifié par glob `src/**/*`). On s'en inspire sans les copier aveuglément.
- assumption: Conflit de conventions JSDoc : `AGENTS.md §1` exige JSDoc sauf `src/lib/`, où `src/lib/AGENTS.md` dit « Pas de JSDoc, un `export default` obligatoire, fonctions pures ». On suit la convention locale pour le nouveau module (pas de JSDoc, `export default` obligatoire, pur sans I/O).
- assumption: Aucune question BLOQUANTE — les captures fixent le contrat (validation stricte, 404, clipping, mitoyenneté).

## Files to touch
| File | Change | Why |
|---|---|---|
| `src/lib/availability.ts` | Créer : `parseDay` + `computeFreeSlots` + `export default` | Logique pure (un module par responsabilité), réutilisable et testable sans Express |
| `src/routes/rooms.ts` | Ajouter `GET /:id/availability` | Point d'entrée HTTP ; 404 salle inconnue + 400 date via `ValidationError` comme `bookings.ts:59-62` |
| `test/availability.spec.ts` | Créer : tests unitaires lib | Couvre `parseDay` et `computeFreeSlots` (trous, fusion, clipping) sans HTTP |
| `test/rooms-availability.spec.ts` | Créer : tests intégration route | Couvre le contrat HTTP avec `createApp()+listen(0)+fetch` comme `test/bookings.spec.ts:4-14` |

## Steps
### 1. Créer la logique pure des créneaux libres
- What: Nouveau `src/lib/availability.ts` avec `Slot { startsAt: string; endsAt: string }`, `DayRange { ok: boolean; value: { start: number; end: number }; error?: string }`, `parseDay(date: string): DayRange` (regex stricte `^\d{4}-\d{2}-\d{2}$` + aller-retour `Date.UTC` pour refuser `2026-02-30`, `05/10/2026` ; `end = Date.UTC(y, m-1, d+1)` donc `2026-12-31 -> 2027-01-01`) et `computeFreeSlots(dayStart: number, dayEnd: number, busy: ReadonlyArray<{ startsAt: string; endsAt: string }>): Slot[]` (parse `Date.parse`, filtre `NaN`, clip `max(start,dayStart)/min(end,dayEnd)`, garde `start < end`, trie par `start`, curseur `cursor=dayStart` : si `b.start > cursor` pousse `{ toIso(cursor), toIso(b.start) }` avec `toIso = new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z")` puis `cursor = max(cursor, b.end)` — fusionne chevauchements et mitoyennetés ; pousse le reliquat si `cursor < dayEnd`). `export default computeFreeSlots`. Import relatif `.js` si besoin, aucune dépendance, aucune JSDoc (convention locale).
- Where: `src/lib/availability.ts` (fichier nouveau ; modèle : `captures/avant/availability.ts:1-75`, `src/lib/overlap.ts:1-14`)
- Done when: `npx tsc --noEmit` passe et `node -e "import('./dist/lib/availability.js')"` (après build) ou test de l'étape 3 passe ; `npm run lint` sans erreur sur le fichier.

### 2. Exposer GET /rooms/:id/availability dans le routeur rooms
- What: Dans `src/routes/rooms.ts`, ajouter après `GET /:id` un `roomsRouter.get("/:id/availability", ...)` qui : 1) `findRoom(req.params.id)` -> `404 { error: "salle inconnue" }` si absent (identique à `src/routes/rooms.ts:10-15`) ; 2) lit `req.query.date`, exige `string` non vide de forme `YYYY-MM-DD` calendairement valide via `parseDay` (import `../lib/availability.js`) -> sinon `throw new ValidationError(...)` rattrapé par `try/catch (err instanceof ValidationError) -> 400 { error }` comme `src/routes/bookings.ts:58-64` (cas `date` absente, tableau, `05/10/2026`, `2026-02-30`) ; 3) `bookingsForRoom(room.id)` -> `computeFreeSlots(start, end, bookings)` -> `200 { roomId, date, freeSlots }`. JSDoc d'une ligne sur le handler si c'est une fonction exportée, sinon rien ; imports relatifs en `.js`.
- Where: `src/routes/rooms.ts:17` (ajout après le bloc `GET /:id`)
- Done when: `curl` manuel via `npm start` ou `npx tsx` : `/rooms/salle-a/availability?date=2026-10-05` -> `200` avec 2 créneaux `00:00-09:00` + `11:00-00:00` ; `/rooms/cave/availability?date=2026-10-05` -> `404` ; sans `date` -> `400`. `npm run lint` passe.

### 3. Ajouter les tests unitaires de la lib
- What: Nouveau `test/availability.spec.ts` reprenant `captures/avant/availability.spec.ts:1-113` : `parseDay` (bornes `2026-10-05`, passage année `2026-12-31 -> 2027-01-01`, refus `05/10/2026` et `2026-02-30`) ; `computeFreeSlots` (vide -> journée entière ; 1 résa 09-11 -> 2 trous ; mitoyennes 09-10+10-11 -> pas de trou ; chevauchantes -> fusion ; venue de la veille et débordement lendemain -> clipping ; hors journée -> ignorée ; journée pleine -> `[]`).
- Where: `test/availability.spec.ts` (fichier nouveau)
- Done when: `npm test -- test/availability.spec.ts` passe (8+4 cas verts).

### 4. Ajouter les tests d'intégration de la route
- What: Nouveau `test/rooms-availability.spec.ts` reprenant `captures/avant/rooms-availability.spec.ts:1-68` avec helper `get()` `createApp()+listen(0)+fetch` comme `test/bookings.spec.ts:4-14` : `salle-a 2026-10-05` -> `200 { roomId, date, freeSlots: [00-09, 11-00] }` (seed `src/store.ts:25-34`) ; `salle-b 2026-10-05` -> journée entière ; `amphi 2026-10-05` -> journée entière (ignore autres salles/jours, seed `2026-10-06`) ; `cave` -> `404` ; sans `date` -> `400` ; `date=05/10/2026` -> `400` ; `date=2026-02-30` -> `400`.
- Where: `test/rooms-availability.spec.ts` (fichier nouveau)
- Done when: `npm test -- test/rooms-availability.spec.ts` passe (7 cas verts) et `npm test` complet reste vert.

## How this is verified
- `npm test` (vitest run, `test/**/*.spec.ts`) vert, dont les 2 nouveaux fichiers ; cas limites exigés : date absente/tableau/mal formée/calendairement inexistante -> `400`, salle inconnue -> `404`, journée vide -> 1 créneau `[00:00, lendemain 00:00[`, trous exacts autour de `09:00-11:00`, mitoyenneté `10:00` sans trou parasite (cohérent avec `overlaps` `[début, fin[` de `src/lib/overlap.ts:4-11`), clipping des bookings à cheval sur minuit, `2026-12-31 -> 2027-01-01`.
- `npm run lint` vert (imports `.js`, `export default` présent dans `src/lib/availability.ts`, pas de dépendance ajoutée).
- `npm run build` vert (`tsc -p tsconfig.build.json`, sortie `dist/` sans erreur).
- Vérification manuelle : `npm start` puis `GET /rooms/salle-a/availability?date=2026-10-05` rend le JSON exact de la capture.

## Risks and rollback
- Risque : divergence de format (`freeSlots` vs `slots`, millisecondes `.000Z` vs `Z`) — atténué en figeant `toIso` sans millisecondes et le contrat `{ roomId, date, freeSlots }` dans les tests d'intégration avant d'implémenter.
- Risque : ordre des routes Express (`/:id` capte `/availability` si placé après une route générique) — atténué car `/:id/availability` a 2 segments, pas de conflit avec `GET /:id` ; vérifier par le test `404 cave` + `200 salle-a`.
- Risque : `Date.parse` fuseau local — atténué en ne manipulant que des ISO `Z` + `Date.UTC`/`toISOString`, jamais de `Date` dans le JSON.
- Rollback : supprimer `src/lib/availability.ts`, `test/availability.spec.ts`, `test/rooms-availability.spec.ts` et le bloc ajouté dans `src/routes/rooms.ts` (aucun impact sur `src/store.ts` qui n'est jamais modifié) ; `npm test` revient à l'état initial.
