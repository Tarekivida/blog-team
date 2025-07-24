# 🧠 blog-team – Génération collaborative d’articles par agents IA

Ce projet Python vise à automatiser la rédaction d’articles de blog structurés, grâce à une **équipe d'agents IA** spécialisés. Chaque agent a une mission définie dans la chaîne de production éditoriale, inspirée d’un vrai fonctionnement en rédaction.

---

## 📚 Objectif

Créer des contenus longs, optimisés SEO, cohérents et pertinents à partir d’une simple idée, d’un mot-clé ou d’un thème. Ce système est particulièrement adapté pour :

- les entreprises (ex : officines, PME, e-commerce),
- les content marketers souhaitant automatiser leur production,
- les équipes souhaitant tester des logiques de prompt chaining ou d’auto-organisation d'agents IA.

---

## 🧩 Architecture modulaire

Chaque **agent** est une fonction spécialisée, qui reçoit un prompt structuré et renvoie un résultat formaté. Voici les rôles :

### 🖋️ 1. `Writer Agent`
- Génère une première version de l’article à partir du mot-clé ou du brief.
- Structure généralement l’article en plusieurs parties (introduction, H2, conclusion).
- Ton informatif ou conversationnel selon configuration.

### 🧭 2. `Content Director Agent`
- Reçoit la version brute du writer.
- Améliore la cohérence narrative, ajuste la tonalité (expertise, bienveillance, curiosité).
- Reformule les titres pour plus d’impact SEO.

### 🔍 3. `Researcher Agent` *(optionnel mais recommandé)*
  - Effectue une recherche web contextuelle.
  - Utilise l'API [Serper.dev](https://serper.dev) pour interroger Google Search de façon programmatique.
  - Peut aussi fonctionner avec une API de recherche locale (comme `searxng`) déployée via Docker.
  - Fournit des extraits, liens et faits pertinents exploitables par le Writer.
  - Peut être rappelé plusieurs fois dans le process à la demande du Content Director.

### 🛠️ 4. `SEO Reviewer Agent`
- Relit l’article pour optimiser le référencement :
  - mots-clés dans les titres,
  - lisibilité (phrases courtes, bullet points),
  - structure H1 > H2 > H3 respectée.
- Évite les répétitions et fluffs.

---

## ⚠️ Problème courant avec les modèles locaux : la **"Thank You Loop"**

Quand vous utilisez des LLM locaux (comme LLaMA3, Mistral, etc.) au lieu de GPT-4, vous pouvez observer un comportement appelé **"thank you loop"** :

> L’agent se met à répondre :  
> *"Thank you for the prompt. Here is the summary..."*  
> *"Thank you for the summary. Here is my opinion..."*  
> etc.

Ce phénomène peut apparaître dans des architectures auto-gérées avec plusieurs agents qui **s’envoient mutuellement leur sortie comme entrée** sans mécanisme de contrôle du contexte.  
Il crée une **boucle infinie de gratitude ou de répétitions non créatives**.

### 🛡️ Solutions possibles :

- Filtrer ou réécrire les réponses contenant `"thank you"` dans le pipeline.
- Limiter les tours de boucle ou introduire un `System Prompt` clair pour chaque rôle.
- Favoriser des modèles comme GPT-4 ou Claude pour les étapes critiques (réécriture, direction éditoriale).
- Éviter que deux agents "dialoguent" en boucle sans intervention externe.

---

## 🛠️ Configuration

Tout se configure depuis `utils/llm_configs.py` :

- Liste des modèles disponibles (GPT-4, LLaMA3, Mistral…)
- `config_list` permet de définir l’ordre de priorité
- Vous pouvez utiliser des modèles locaux via `LM Studio` (en localhost) ou des API distantes

---

## 🏁 Utilisation

```bash
python3 main.py