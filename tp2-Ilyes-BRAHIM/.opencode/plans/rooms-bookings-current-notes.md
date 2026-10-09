# Notes explorer — endpoints rooms & bookings (etat courant)

## Answer
L'API est une app Express montee dans `src/app.ts`, avec deux routeurs (`/rooms`,
`/bookings`) qui lisent/ecrivent directement les tableaux en memoire de `src/store.ts`.
`/rooms` est en lecture seule ; `/bookings` porte la validation (POST) et la suppression.
Les erreurs de validation sont des exceptions `ValidationError` (status 400) attrapees
dans le handler POST. Aucun endpoint `/availability` n'existe dans `src/` a ce jour.

## How it works
1. `src/server.ts:5` cree l'app via `createApp()` et ecoute `PORT` (defaut 3000,
   `src/server.ts:3`). `src/app.ts:5-11` monte `express.json()`, `/health`, puis les
   deux routeurs.
2. Store memoire : `rooms` (4 salles amorcees, `src/store.ts:18-23`) et `bookings`
   (2 reservations amorcees, `src/store.ts:25-44`), plus `seq = 1002`
   (`src/store.ts:46`). Helpers `nextBookingId` (`:48`), `findRoom` (`:53`),
   `bookingsForRoom` (`:57`). Les tableaux sont exportes et **mutes en place**.
3. `GET /rooms` renvoie `{ rooms }` (`src/routes/rooms.ts:6-8`).
4. `GET /rooms/:id` -> `findRoom` ; 404 `{error:"salle inconnue"}` si absent
   (`rooms.ts:12-15`), sinon `{ room, bookings: bookingsForRoom(room.id) }`
   (`rooms.ts:16`).
5. `GET /bookings` filtre sur `?roomId` (string) sinon renvoie tout
   (`src/routes/bookings.ts:9-16`).
6. `POST /bookings` (`bookings.ts:18`) : extrait roomId/who/people/startsAt/endsAt via
   `requireString`/`requirePositiveInt`/`requireDate` (`:21-25`), verifie
   `endsAt > startsAt` (`:27`), existence salle (`:31-34`), capacite (`:35-37`).
7. Conflit de creneau : `overlaps(...)` sur les reservations de la salle
   (`bookings.ts:39-41`), 409 `{error:"creneau deja reserve", conflictsWith}` (`:43`).
8. Sinon construit le booking avec `price: priceFor(room, startsAt, endsAt)` (`:54`),
   `push` dans le tableau (`:56`), 201 `{ booking }` (`:57`).
9. `DELETE /bookings/:id` : `findIndex` ; 404 si absent (`bookings.ts:69-71`), sinon
   `splice` et `{ cancelled: id }` (`:73-74`).

## Dates / prix / chevauchement
- Dates = string ISO 8601 UTC (`src/store.ts:13-14`, AGENTS.md:25). Aucun `Date` stocke.
- `requireDate` valide via `Date.parse` non-NaN (`src/lib/validate.ts:16-22`).
- `priceFor = hourlyRate * hoursBetween`, +20 si `isWeekend(startsAt)` (samedi/dimanche
  UTC) (`src/lib/price.ts:6-21`). `hoursBetween` = diff ms / 3600000 (`:11-13`).
- `overlaps` : intervalles semi-ouverts `[debut, fin[` -> `a1 < b2 && b1 < a2`
  (`src/lib/overlap.ts:6-11`). Bornes mitoyennes ne se chevauchent pas (test
  `overlap.spec.ts:27-36`, `bookings.spec.ts:68-86`).

## ValidationError -> 400
- `ValidationError extends Error` avec `status = 400` (`validate.ts:4-6`).
- Le POST enveloppe tout dans `try/catch` (`bookings.ts:19,58`) : si
  `err instanceof ValidationError`, `res.status(err.status).json({error: err.message})`
  (`:59-61`) ; sinon `throw err` (`:63`) -> 500 Express par defaut.
- Note : salle inconnue en POST est une ValidationError -> **400** (`bookings.ts:33`),
  alors qu'en GET `/rooms/:id` c'est un **404** (`rooms.ts:13`). Test POST attend 400
  (`bookings.spec.ts:24-33`).

## Tests
- `vitest run` (`package.json:10`), config `include: ["test/**/*.spec.ts"]`,
  `environment: "node"` (`vitest.config.ts:5-9`). Convention `*.spec.ts`.
- Tests d'integration : `createApp()`, `app.listen(0)`, `fetch` sur 127.0.0.1 puis
  `server.close()` dans `finally` (`bookings.spec.ts:4-14`).
- Tests unitaires directs sur `src/lib` (`overlap.spec.ts`, `price.spec.ts`) et store
  (`store.spec.ts`). Un test skip documente une fixture absente
  (`overlap.spec.ts:60-74`).

## Key files
- src/app.ts:5-11 — composition de l'app et montage des routeurs
- src/routes/rooms.ts:1-17 — GET /rooms et /rooms/:id
- src/routes/bookings.ts:1-75 — GET/POST/DELETE /bookings
- src/store.ts:1-59 — types + donnees memoire + helpers
- src/lib/validate.ts:1-30 — ValidationError et require*
- src/lib/price.ts:1-23 — tarification + export default
- src/lib/overlap.ts:1-14 — chevauchement + export default
- test/bookings.spec.ts:1-87 — spec representatif d'integration
- vitest.config.ts:5-9 — inclusion des tests

## Gotchas
- Le store est **mute en place** : les tests qui POST ajoutent des bookings au tableau
  global partage entre tests (pas de reset). `bookings.spec.ts` utilise des salles/dates
  distinctes pour eviter les collisions, mais c'est implicite.
- `nextBookingId` (`store.ts:48`) est un compteur global non reinitialise.
- `src/lib/AGENTS.md:5` exige un `export default` par module ; `price.ts:23` et
  `overlap.ts:14` l'ont, mais `validate.ts` n'en a **pas** (consomme par imports nommes
  seulement). L'AGENTS racine `:5` exige une JSDoc sur toute fonction exportee, sauf
  `src/lib/` (`src/lib/AGENTS.md:8`).
- `captures/avant/availability.ts` et les specs `captures/avant/*` decrivent un endpoint
  `/rooms/:id/availability` + `src/lib/availability.ts` qui **n'existent pas** dans
  `src/` : c'est une capture, pas le code courant.
- `parseDay` de la capture utilise un `Date.UTC(year, month-1, day)` avec `day` brut, pas
  `day-1` — code non branche, a ne pas confondre avec l'etat courant.
- AGENTS.md:32 interdit de toucher `src/store.ts` (remplace par INFRA-140).

## Unknowns
- Aucun test d'integration pour GET /rooms ni DELETE /bookings (non couverts ici).
- Je n'ai pas execute `npm test` (bash restreint) : l'etat vert/rouge de la suite n'est
  pas verifie, seulement lu.
- `captures/avant/` : je n'ai pas determine par quel ticket/process ces fichiers sont
  produits ni s'ils sont destines a etre deplaces dans `src/` (probable capture TDD
  avant implementation).
