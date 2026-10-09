# Captures — preuves du diagnostic

Les preuves sont des **images PNG** (`captures/**/*.png`). Chacune est le rendu de la
sortie terminal de la commande correspondante. La machine de travail n'ayant pas
d'environnement graphique, ce sont des rendus de terminal et non des captures d'écran au
sens strict ; le contenu (commandes, sorties, codes) est brut.

| Fichier | Ce qu'il prouve |
|---|---|
| `avant/git-status.png` | état du dépôt après le run « avant » de la chaîne |
| `avant/diff-avant.png` | code produit par la chaîne « avant » |
| `avant/availability.png`, `avant/*.spec.png` | fichiers créés par la chaîne « avant » |
| `avant/chain-errors.png` | `ProviderModelNotFoundError` : les subagents échouaient tous |
| `avant/tests-hidden-failures.png` | bugs révélés en renommant les tests cachés (409 vs 201, `'5020'` vs 70) |
| `02-tests-corriges.png` | suite verte après correction des tests et des bugs |
| `03-lint-actif.png` | le lint attrape enfin une erreur (avant : `rules: {}`) |
| `04-hook-precommit.png` | le pre-commit husky s'exécute réellement à chaque commit |
| `05-commit-harness.png` | commit du harness réparé (hook vert) |
| `06-apres-chain.png` | run « après » : délégation finder/explorer/planner/dev/reviewer/tester |
| `07-apres-tests.png` | 38 tests verts après le run « après » |
| `08-commit-feature.png` | commit de la fonctionnalité produite par la chaîne |
| `09-commit-diag.png` | commit du présent diagnostic |

Le raisonnement complet est dans `DIAGNOSTIC.md` à la racine du dépôt.
