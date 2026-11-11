# CLAUDE.md — blog-team

Document de reprise à froid. Rédigé le 2026-11-11 à partir de l'exploration du dépôt (code, branches, historique, .gitignore, venv local).
Ce qui n'a pas pu être vérifié est marqué **inconnu**.

> **ALERTE SÉCURITÉ** : une clé API Serper.dev est écrite en dur dans `main.py` et `example.py` (variable `SERPER_API_KEY` dans `main()`), et ces fichiers sont poussés sur GitHub. La clé doit être considérée comme compromise : la révoquer/régénérer sur https://serper.dev, la remplacer par `os.environ["SERPER_API_KEY"]`, et envisager de purger l'historique git si le repo est public.

## 1. Objectif et contexte

- Script Python qui **rédige un article de blog en français** à partir d'un sujet saisi au clavier, via une petite équipe d'agents **AutoGen** (`pyautogen` 0.9.0).
- Public des articles : **pharmaciens d'officine français à profil entrepreneurial** (contenu business / croissance de l'officine, optimisé SEO).
- Le README (en français) présente le projet de manière plus générique (entreprises, content marketers, test de prompt chaining).
- Utilisateur du script : l'auteur, en local, terminal. Pas d'UI, pas de déploiement.
- Le projet est un **dérivé de `development_team`** (même historique initial, voir §3). Dépôt : `https://github.com/Tarekivida/blog-team.git`.

## 2. Stack

- Python **3.13** (venv local).
- `pyautogen==0.9.0`, `openai==1.76.2`, `requests`, **`beautifulsoup4` (importé mais absent du venv local et d'aucun requirements → à installer)**.
- Le venv local contient aussi Flask, Flask-SocketIO, FastAPI, uvicorn, gunicorn, eventlet : **non utilisés par le code** (vestiges d'essais d'UI web, cf. spec UI dans `development_team`).
- LLM : `config_list` dans `utils/llm_configs.py` — `gpt-4` OpenAI en premier (clé **placeholder** `"your-openai-api-key"`), puis une série de modèles servis par **LM Studio** en local (`http://localhost:1234/v1`, API compatible OpenAI) : mistral-7b, llama-3-8b-instruct, llama3.1-8b, mixtral, phi3, qwen-7b, nous-hermes-2-mistral, dolphin-mistral, flux-prompt, llama3.2-3b, gemma-3-12b-it-qat.
- Recherche web : API **Serper.dev** (Google Search) + scraping `requests` + BeautifulSoup (paragraphes `<p>`).

## 3. Branches et historique

| Branche | Contenu |
|---|---|
| `main` (locale, checkée, = `origin/main`, branche par défaut) | Le vrai projet blog-team. Commits : `b5020fe` « Initial commit of blog-team » (2025-07-24) puis `9b67c46` « Ignore .DS_Store » (2026-11-11). |
| `origin/tester-agent` (distante uniquement, pas de branche locale) | Pointe sur `749fce9` (2025-05-01) : c'est **exactement l'état initial du projet `development_team`** (agents Admin/Project_Manager/Engineer, `requirements.txt`, LICENSE MIT). C'est aussi l'ancêtre commun de `main` (`git merge-base` = `749fce9`). Pas de travail spécifique « tester » dessus ; son nom est hérité. |

Conséquences : `main` a **supprimé** `LICENSE` et `requirements.txt` par rapport à l'ancêtre. Pour consulter l'ancienne version : `git show origin/tester-agent:main.py`.

## 4. Arborescence commentée (`main`)

```
blog-team/
├── main.py              # Script principal (pipeline Writer → ContentDirector → Researcher/Writer → Reviewer)
├── example.py           # Variante antérieure/alternative de main.py (prompts plus génériques : brouillon en 1 paragraphe, règles détaillées pour appeler le Researcher). Même structure.
├── utils/llm_configs.py # Liste des configs LLM (OpenAI + LM Studio) ; l'ordre de config_list = priorité
├── readme.md            # README français (rôles des agents, problème de la « thank you loop »)  [apparaît comme README.md sur macOS, insensible à la casse]
├── .cache/41/cache.db   # Cache disque SQLite d'AutoGen (diskcache) — SUIVI PAR GIT par erreur (~340 Ko)
└── .gitignore
```

Hors git : `.venv/`, `output/` (articles générés), `__pycache__/`, `.DS_Store`.

## 5. Architecture et flux (main.py)

1. `input()` : sujet de l'article → nom de fichier assaini (`[^a-zA-Z0-9_]` supprimés).
2. `collect_external_knowledge(topic, key)` : requête Serper (`https://google.serper.dev/search`, 5 résultats organiques) → téléchargement de chaque URL → texte des `<p>` (≥ 200 caractères, tronqué à 1000).
3. `summarize_knowledge()` : l'agent Writer résume les extraits (≤ 8 lignes) via `generate_reply`.
4. Construction des « guidelines » = résumé + extraits bruts → premier message.
5. Agents :
   - **Writer** : rédige le brouillon (pharmaciens entrepreneurs), intègre les recherches.
   - **ContentDirector** : feedback critique sans réécrire ; termine par un tag unique `#validé`, `#neededresearch` ou `#noneededresearch`.
   - **Researcher** : répond uniquement à la section « Ce qui doit être cherché » (il n'a **pas** d'outil de recherche : il répond depuis le LLM).
   - **Reviewer** : relecture SEO finale.
6. `StrictWorkflowManager(GroupChatManager).on_message()` : routage déterministe Writer → ContentDirector → (Researcher si `#neededresearch`, Writer si `#noneededresearch`, Reviewer si `#validé`) ; Researcher → Writer ; Reviewer → fin.
7. Boucle manuelle (30 itérations max) autour de `manager.initiate_chat(...)` avec de nombreuses protections anti-boucle (même rôle deux fois de suite, réponse vide, etc.).
8. Écriture de `output/<sujet>.md` puis affichage d'un résumé de conversation et `TERMINATE`.

## 6. Installation et lancement

```bash
git clone https://github.com/Tarekivida/blog-team.git && cd blog-team
python3 -m venv .venv && source .venv/bin/activate
# requirements.txt n'existe plus sur main : on peut repartir de celui de l'ancêtre
git show origin/tester-agent:requirements.txt > /tmp/req-blog.txt && pip install -r /tmp/req-blog.txt
pip install beautifulsoup4
# LLM : soit renseigner une vraie clé OpenAI dans utils/llm_configs.py (à remplacer par une variable d'env),
#       soit démarrer LM Studio (serveur local port 1234) avec un modèle chargé et mettre sa config en tête de config_list
python3 main.py          # puis saisir le sujet, ex. « Comment utiliser ChatGPT en pharmacie »
```

Pas de tests, pas de build, pas de CI, pas de déploiement.

## 7. Variables d'environnement / secrets et services externes

Le code **ne lit aucune variable d'environnement** aujourd'hui. Variables recommandées lors de la reprise :

| Nom (à introduire) | Rôle | Où l'obtenir |
|---|---|---|
| `SERPER_API_KEY` | Recherche Google via Serper.dev (actuellement en dur dans le code, voir alerte) | https://serper.dev (dashboard → API key) |
| `OPENAI_API_KEY` | Modèle `gpt-4` (actuellement placeholder en dur dans `utils/llm_configs.py`) | https://platform.openai.com/api-keys |

Services : Serper.dev, OpenAI (optionnel), LM Studio local (aucune clé, `api_key: "not-needed"`), sites web scrapés (User-Agent Chrome falsifié).

## 8. Données et fichiers exclus de git

- `output/` : articles générés (`.md`). Localement il n'y a qu'un exemple, `Comment_utiliser_chatgpt_en_pharmacie.md`. Régénérables en relançant le script ; rien de précieux.
- `.venv/` : à recréer.
- À l'inverse, `.cache/41/cache.db` **est** suivi par git alors qu'il devrait être ignoré (cache AutoGen ; peut contenir des prompts/réponses LLM passés). Peut être supprimé sans risque.

## 9. État, TODO, bugs connus

État : prototype expérimental, dernier travail de fond en juillet 2025.

Bugs / faiblesses constatés :
- **Le routage ne fonctionne probablement pas** : le code compare `message["role"]` à `"writer"`, `"contentdirector"`, etc., or dans AutoGen le champ `role` vaut `user`/`assistant` et le nom de l'agent est dans `message["name"]`. Indice concret : l'article de sortie local (`output/Comment_utiliser_chatgpt_en_pharmacie.md`) ne contient que les « guidelines » initiales (résumé + extraits web), pas d'article rédigé → le workflow s'arrête avant que les agents produisent un résultat (`final_article = last_content`). À corriger en utilisant `name`.
- `final_article` peut être non défini si la boucle de 30 tours s'épuise sans `break` → `NameError`.
- Le Researcher n'a pas d'outil web : il « invente » ses sources à partir du LLM.
- `openai_config` en tête de liste avec une clé placeholder → échec d'authentification ; le repli sur LM Studio dépend du comportement de fallback d'AutoGen (non vérifié).
- `beautifulsoup4` manquant du venv et de toute liste de dépendances ; `requirements.txt` supprimé.
- `.gitignore` : ligne `.DS_Store.DS_Store` (concaténation accidentelle) → `.DS_Store` n'est pas réellement ignoré à la racine ; des `.DS_Store` non suivis apparaissent dans `git status`.
- Clé Serper en dur (voir alerte).
- `example.py` duplique ~95 % de `main.py` ; lequel est la référence n'est pas documenté (main.py est le plus récent en termes de prompts « pharmacien entrepreneur »).
- README tronqué à la fin (bloc de code « Utilisation » non fermé).

TODO implicites (README) : recherche via SearxNG en Docker comme alternative à Serper ; atténuer la « thank you loop » des modèles locaux.

## 10. Conventions, décisions, pièges

- Prompts et logs en **français** ; tags de contrôle en minuscules (`#validé` avec accent).
- Le choix du modèle se fait **uniquement par l'ordre de `config_list`** dans `utils/llm_configs.py`.
- « Thank you loop » : problème documenté des modèles locaux qui se remercient en boucle → raison d'être du `StrictWorkflowManager` et des garde-fous anti-boucle.
- `cache_seed: None` → pas de cache déterministe (pourtant un `.cache/` existe d'une version antérieure).
- Sur macOS, `readme.md` et `README.md` désignent le même fichier ; git suit `readme.md`.

## 11. Reprendre le projet

1. Révoquer la clé Serper exposée ; passer la clé en variable d'environnement (`SERPER_API_KEY`) et la clé OpenAI aussi.
2. Recréer un `requirements.txt` (pyautogen 0.9.0, openai, requests, beautifulsoup4) et l'ajouter au repo.
3. Corriger `.gitignore` (`.DS_Store`, `.cache/`) et retirer `.cache/` du suivi (`git rm --cached`).
4. Corriger le routage (`message["name"]` au lieu de `message["role"]`), initialiser `final_article`.
5. Tester avec un modèle fiable (gpt-4o/Claude) avant de revenir aux modèles locaux.
6. Choisir entre `main.py` et `example.py` et supprimer le doublon.
7. Décider du sort de `origin/tester-agent` (simple copie de l'ancien `development_team`, peut être supprimée côté GitHub).
