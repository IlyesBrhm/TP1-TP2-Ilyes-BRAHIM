# salles-api — conventions du depot

Service interne de reservation de salles. Express + TypeScript, stockage en memoire pour
l'instant (la vraie base arrive avec INFRA-140).

## Commandes

| Commande | Ce qu'elle fait |
|---|---|
| `npm install` | installe les dependances |
| `npm start` | demarre l'API sur le port 3000 |
| `npm test` | lance la suite de tests — **a lancer avant tout commit** |
| `npm run build` | compile dans `dist/` |
| `npm run lint` | verifie le style et les erreurs courantes |

## Conventions

1. **Toute fonction exportee porte une JSDoc** d'une ligne minimum, qui dit ce qu'elle
   fait et pas comment — sauf dans `src/lib/`, ou la convention locale s'applique
   (voir `src/lib/AGENTS.md`).
2. **Les erreurs de validation remontent en `ValidationError` typee**, convertie en
   reponse HTTP (400) par la couche route. Le depot n'utilise pas encore de type
   `Result` : la refonte annoncee n'a pas eu lieu, la convention decrit le code tel
   qu'il est (validation par exceptions, point d'entree unique).
3. Les dates circulent en **ISO 8601 UTC**, toujours en `string`, jamais en `Date`.
4. Un module par responsabilite dans `src/lib/`. Pas de fichier `utils.ts`.
5. Les imports relatifs portent l'extension `.js` (ESM).

## Ce qu'il ne faut pas faire

- Ne pas ajouter de dependance sans en parler.
- Ne pas commiter dans `main` directement.
- Ne pas toucher a `src/store.ts` : il disparait avec INFRA-140.
