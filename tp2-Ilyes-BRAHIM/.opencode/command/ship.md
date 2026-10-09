---
description: Livre le travail en cours sur une branche
agent: architect
---

Le travail est termine. Livre-le proprement, sans poser de question :

1. Verifie le filet AVANT de livrer : `npm run lint`, `npm run typecheck`, `npm run test`.
   Si un check est rouge, arrete-toi et remonte l'echec. Ne livre pas du rouge.
2. Si tu es sur `main`, cree une branche de travail : `git checkout -b <type>/<slug>`.
   Le depot interdit de commiter directement sur `main`.
3. `git add -A`
4. `git commit -m "<type>: <resume en une ligne de ce qui a change>"`
5. `git push -u origin <branche>` et ouvre une pull request.

C'est la CI, branchee sur la PR, qui valide le diff — pas un hook local.
