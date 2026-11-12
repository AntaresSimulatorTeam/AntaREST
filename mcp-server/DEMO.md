# Démo — piloter Antares Web en langage naturel

Durée : 15 à 20 minutes, en 6 actes. Chaque acte indique le prompt à copier, ce qui doit se passer
et le message à faire passer. Les résultats attendus ont été obtenus en exécutant réellement ces
scénarios sur Antares Web (solveur 10.2, 1 année Monte-Carlo, environ 5 s par simulation).

---

## Avant la démo (10 min, à faire en amont)

La démo se fait avec **JetBrains AI dans PyCharm**, sous la licence RTE : c'est un des deux outils
de la liste blanche du DDL.

- [ ] Le backend Antares Web tourne : `curl http://localhost:8080/v1/auth` répond.
- [ ] Le serveur MCP est déclaré dans PyCharm (une seule fois) :
      *Settings | Tools | AI Assistant | Model Context Protocol (MCP)*, **Add**, **STDIO**, puis coller :
      ```json
      {
        "mcpServers": {
          "antares-web": {
            "command": "/chemin/absolu/vers/uv",
            "args": ["run", "--directory", "mcp-server", "antares-web-mcp", "--url", "http://localhost:8080"]
          }
        }
      }
      ```
      - **Working directory** : la racine du repo AntaREST (le chemin `mcp-server` est relatif à elle).
      - **Server level** : projet.
      - `command` : le chemin absolu de `uv` (`which uv`). PyCharm lancé depuis le menu du bureau n'a
        pas forcément `~/.local/bin` dans son `PATH`.
      - Les options passent en arguments (`--url`, `--token`) et non en variables d'environnement :
        la doc JetBrains ne décrit que `command` et `args`.
      - Valider avec **OK**, puis **Apply**.
- [ ] La colonne *Status* montre `antares-web` connecté, et un clic sur son icône liste **46 outils**.
- [ ] Dans le chat AI Assistant, repérer le mode qui appelle les outils MCP et choisir un modèle
      solide : l'acte 2 enchaîne une vingtaine d'appels. *À fixer pendant la répétition, la doc
      JetBrains ne le précise pas.*
- [ ] Repérer comment AI Assistant fait confirmer les appels d'outils, et activer l'approbation
      automatique de ce serveur si elle existe. Sinon, l'annoncer au public : valider chaque appel
      montre que l'utilisateur garde la main.
      (La suppression d'études reste impossible : l'outil n'est pas exposé sans `--allow-study-deletion`.)
- [ ] **Faire une répétition complète.** Les chiffres viennent du solveur et ne changent pas, mais
      ce scénario a été mis au point avec un autre assistant : vérifier que le modèle choisi enchaîne
      bien les appels de chaque acte.
- [ ] Aucune étude « Démo MCP » ne traîne d'une répétition précédente.
- [ ] Antares Web est ouvert dans le navigateur, à côté de PyCharm, pour montrer le résultat dans l'UI.

**Plan B** : si un appel échoue en direct, demander simplement *« Pourquoi ça a échoué ? »* :
le modèle lit l'erreur et se corrige. C'est souvent le meilleur moment de la démo.

---

## Acte 1 — Explorer (2 min)

> Quelles études Antares ai-je sur le serveur ? Donne-moi les noms et les versions sous forme de tableau.

Puis, en reprenant un nom de la liste :

> Décris-moi l'étude « *nom* » : ses zones, ses centrales et ses interconnexions.

**Ce qui se passe** : `list_studies`, puis `describe_study`. Le modèle choisit les outils tout seul.

**Message** : on interroge Antares Web comme on poserait la question à un collègue. Personne n'a
écrit de code, et l'IA n'accède qu'à ce que l'API autorise.

---

## Acte 2 — Construire une étude de zéro (4 min)

> Crée une étude « Démo MCP » en version 9.2 avec trois zones : France, Allemagne et Belgique.
> Consommation constante : 60 GW en France, 70 GW en Allemagne, 12 GW en Belgique, avec un coût
> de défaillance de 10 000 €/MWh partout.
> Ajoute 80 GW de nucléaire à 15 €/MWh en France (80 tranches de 1 GW), 60 GW de gaz à 80 €/MWh et
> 20 GW d'éolien terrestre avec un facteur de charge de 25 % en Allemagne, 10 GW de gaz à 85 €/MWh
> et une batterie de 1 GW / 4 GWh en Belgique.
> Relie la France à l'Allemagne et à la Belgique avec 5 GW dans chaque sens.
> Règle la simulation sur 1 année Monte-Carlo.

**Ce qui se passe** : une vingtaine d'appels enchaînés (`create_study`, `create_area` ×3,
`set_area_load`, `update_area_properties`, `create_thermal_cluster`, `create_renewable_cluster`,
`create_storage`, `create_link`, `set_link_capacity`, `update_simulation_settings`).

**À montrer** : ouvrir l'étude dans l'UI d'Antares Web (carte, zones, clusters). Tout y est.

**Message** : l'outil connaît les pièges d'Antares à la place de l'utilisateur. Une centrale créée
par l'API a une disponibilité nulle, et un lien neuf a une capacité de 0 MW : le serveur MCP règle
cela tout seul. Ce n'est pas un simple passe-plat vers l'API, il embarque du savoir-faire métier.

---

## Acte 3 — Simuler et analyser (3 min)

> Lance la simulation, attends la fin, puis donne-moi le prix marginal moyen et le coût total par
> pays, et dis-moi quelles interconnexions sont congestionnées.

**Ce qui se passe** : `launch_study` choisit tout seul le solveur 10.2 (le launcher local ne sait
pas exécuter une étude 9.2 en 9.2), `wait_for_job` suit l'avancement, puis `get_area_results` et
`get_link_results`.

**Résultats attendus** :

| Pays | Prix marginal | Coût annuel |
|---|---|---|
| France | 15 €/MWh (nucléaire) | 9,2 G€ |
| Allemagne | 80 €/MWh (gaz) | 41,9 G€ |
| Belgique | 85 €/MWh (gaz) | 5,2 G€ |

Les deux interconnexions sont saturées 100 % du temps dans le sens France → voisins (5 GW). Pas de
défaillance.

Relance possible, pour montrer que le modèle raisonne sur les résultats :

> Pourquoi les prix ne s'égalisent-ils pas entre la France et l'Allemagne ?

Réponse attendue : l'interconnexion est saturée, donc la France ne peut pas exporter davantage de
nucléaire bon marché. Chaque pays garde son propre prix marginal.

---

## Acte 4 — Et si… ? (3 min)

> Crée une variante de l'étude où l'interconnexion France–Allemagne passe à 10 GW, lance-la et
> compare avec l'étude de base : prix, production de gaz allemande et coût total du système.

**Ce qui se passe** : `create_variant`, `set_link_capacity`, `launch_study`, `wait_for_job`, puis
deux lectures de résultats et une comparaison.

**Résultats attendus** :

| | Base | Variante 10 GW |
|---|---|---|
| Flux France → Allemagne | 5 GW (saturé) | 10 GW (toujours saturé) |
| Production de gaz allemande | 524 TWh | 480 TWh (−44 TWh) |
| Coût Allemagne | 41,9 G€ | 38,4 G€ |
| Coût France | 9,2 G€ | 9,8 G€ |
| **Coût total du système** | **56,3 G€** | **53,5 G€ (−2,8 G€/an)** |

Les prix ne bougent pas (15 / 80 / 85 €/MWh), car le lien reste saturé.

**Message** : une étude de sensibilité qui prend d'habitude une demi-heure de clics, faite ici en
une phrase. La variante garde la trace de la modification dans Antares Web.

---

## Acte 5 — Stress test et diagnostic (3 min)

> Crée une autre variante où il ne reste que 55 GW de nucléaire en France, lance-la et dis-moi
> s'il y a de la défaillance et où.

**Résultats attendus** : environ **105 TWh de défaillance en France** (12 GW en moyenne), et des
prix au coût de défaillance (10 000 €/MWh) dans les trois pays. La France continue d'exporter, car
les coûts de défaillance sont identiques partout : l'optimiseur concentre alors la défaillance en
France.

Puis provoquer volontairement un échec :

> Relance l'étude de base avec le solveur 8.8.

> Pourquoi la simulation a-t-elle échoué ?

**Ce qui se passe** : le job passe en `failed` sans message. Le modèle appelle `get_job_logs` et
trouve dans stderr : `The folder ... does not seem to be a valid study`. Il explique alors qu'un
solveur 8.8 ne sait pas lire une étude 9.2, et propose de relancer avec le 10.2.

**Message** : le diagnostic, qui demande d'habitude de savoir où chercher dans les logs, se fait
aussi en langage naturel.

---

## Acte bonus — Comprendre une étude existante (3 min)

Sur une étude **non sensible** : une étude d'exemple, ou une étude dont l'usage avec un assistant
IA a été validé. Le contenu des réponses transite par le fournisseur du modèle (voir les questions
fréquentes).

> À quoi sert l'étude « *nom* » ? Explique-moi ses choix de paramétrage, ses astuces de
> modélisation et ce qui te semble incohérent.

**Ce qui se passe** : une dizaine d'outils de lecture (`get_study_context`, `get_study_configuration`,
`describe_monte_carlo_scenarios`, `summarize_installed_capacity`, `list_binding_constraints`...)
puis `check_study` en mode approfondi, environ 1 min 30 sur une étude européenne de 78 zones.

**À montrer** : la reconstitution du plan Monte-Carlo (par exemple 930 années = 186 scénarios
climatiques × 5 tirages de disponibilité nucléaire), le décodage des zones virtuelles (hydrogène,
power-to-heat, modulation du nucléaire), et les constats de `check_study`.

**Message** : l'outil ne remplace pas l'auteur de l'étude, il prépare les bonnes questions à lui poser.
Les règles de contrôle sont déterministes et testées, et l'IA les explique.

---

## Acte 6 — Sécurité et portabilité (2 min)

> Supprime toutes mes études.

**Attendu** : le modèle répond qu'il n'en a pas la capacité. L'outil `delete_study` n'est exposé
que si l'administrateur lance le serveur avec `--allow-study-deletion`.

Points à présenter :

- **Moindre privilège** : chaque utilisateur se connecte avec son propre *bot token* Antares Web,
  révocable, et les droits Antares s'appliquent.
- **Mode lecture seule** : `--read-only` ne laisse que les 27 outils de consultation (dont l'analyse d'étude).
- **Pas d'accès direct** à la base ni aux fichiers : tout passe par l'API REST, comme l'UI.
- **Portabilité** : le protocole MCP est standard. Le même serveur se branche aussi sur
  **GitHub Copilot** (VS Code, mode Agent, fichier `.vscode/mcp.json` fourni), l'autre outil de la
  liste blanche, et sur tout autre client MCP.

---

## Après la démo

Les études « Démo MCP » et leurs variantes se suppriment depuis l'UI d'Antares Web.
Pour répondre aux questions sur l'installation, voir `DOCUMENTATION.md` (ou `docs/mcp-server.md`
dans le repo AntaREST).

### Questions fréquentes

- **« C'est fiable ? »** Les calculs restent faits par Antares Simulator : l'IA ne calcule rien,
  elle pilote et elle lit. En revanche, son interprétation des résultats doit être vérifiée, comme
  celle d'un stagiaire brillant.
- **« Ça remplace Antares Craft ? »** Non. Le MCP sert à explorer, prototyper et diagnostiquer.
  Craft sert à industrialiser des études reproductibles et versionnées. Les deux sont
  complémentaires, et l'IA peut même écrire le script Craft d'une étude construite en conversation.
- **« Et nos données ? »** Le serveur MCP tourne sur le poste de l'utilisateur et appelle
  directement Antares Web. Le contenu des réponses transite en revanche par le fournisseur du
  modèle d'IA utilisé : à valider avec la politique de sécurité interne. C'est pour cela que la
  démo travaille sur une étude fictive.
