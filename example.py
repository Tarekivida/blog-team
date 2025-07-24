import autogen
import os
import time
import re
from utils.llm_configs import llm_config
import requests
from bs4 import BeautifulSoup

# --------- Recherche Web & Scraping ---------
def google_search(query, api_key, num_results=5):
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": num_results}
    headers = {"X-API-KEY": api_key}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    return [item['link'] for item in data.get('organic', [])[:num_results]]

def extract_text_from_url(url, max_length=1000):
    try:
        r = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        ps = soup.find_all("p")
        text = "\n".join([p.get_text(strip=True) for p in ps])
        text = ' '.join(text.split())
        if not text or len(text) < 200:
            return None
        return text[:max_length]
    except Exception:
        return None

def collect_external_knowledge(query, api_key, max_sources=5):
    links = google_search(query, api_key, num_results=max_sources)
    all_texts = []
    for idx, link in enumerate(links, 1):
        content = extract_text_from_url(link)
        if content:
            all_texts.append(f"Source {idx}: {link}\n{content}")
    return all_texts

# --------- Agents Setup ---------
writer = autogen.AssistantAgent(
    name="Writer",
    llm_config=llm_config,
    system_message=(
        "Vous êtes rédacteur. Rédigez un premier brouillon d’article basé sur le sujet donné. "
        "Restez concentré sur le sujet, apportez un contenu pertinent et utile à votre audience. "
        "Prenez des initiatives pour structurer et enrichir l’article. "
        "Rédigez un seul paragraphe synthétique. "
        "Si vous recevez un texte provenant du Researcher (résumé de recherche ou sources), vous DEVEZ impérativement l’intégrer, le reformuler ou vous en inspirer explicitement dans votre nouvelle version de l’article. "
        "Mentionnez dans votre rédaction les faits ou sources fournis, et améliorez l’exactitude et la richesse du contenu."
    ),
)

content_director = autogen.AssistantAgent(
    name="ContentDirector",
    llm_config=llm_config,
    system_message=(
        "Vous êtes Content Director, chef d’orchestre éditorial.  \n"
        "Avant d’appeler le Researcher (tag #neededresearch), appliquez STRICTEMENT les règles suivantes :  \n"
        "- Appelez le Researcher UNIQUEMENT si le texte nécessite :  \n"
        "    • Faits, chiffres, statistiques, tendances, études, citations SANS source précise  \n"
        "    • Exemples concrets SANS preuve ou illustration  \n"
        "    • Mentions de marques, entreprises, personnes, nouveautés SANS source/contextualisation  \n"
        "    • Résultats, records, comparatifs, évolutions sectorielles à vérifier/documenter  \n"
        "    • Généralisation de tendances, innovations, pratiques SANS source/exemple récent  \n\n"
        "Dans tous les autres cas (style, structure, clarté, ton, optimisation SEO, feedback éditorial), n’appelez PAS le Researcher et tagguez #noneededresearch.  \n\n"
        "Vous donnez toujours un feedback éditorial.  \n"
        "Vous ne réécrivez jamais le texte.  \n"
        "Terminez toujours votre réponse par UN SEUL tag sur une ligne à part : #validé, #neededresearch, #noneededresearch.  \n"
        "N’ajoutez RIEN d’autre dans la réponse. Respectez toujours ce format."
    ),
)

reviewer = autogen.AssistantAgent(
    name="Reviewer",
    llm_config=llm_config,
    system_message=(
        "Vous êtes relecteur SEO. Votre mission : rendre l’article final optimisé pour le référencement Google, lisible et pertinent pour des pharmaciens en France. "
        "Vous ne touchez qu’à la structure et aux formulations pour améliorer l’impact SEO, sans changer le fond."
    ),
)

researcher = autogen.AssistantAgent(
    name="Researcher",
    llm_config=llm_config,
    system_message=(
        "Vous êtes chercheur. Lors d’un feedback #neededresearch, répondez STRICTEMENT et EXCLUSIVEMENT à la section 'Ce qui doit être cherché' fournie par le Content Director. \n"
        "Ne traitez aucun autre point, même s’il est mentionné ailleurs dans le message. Présentez un résumé synthétique pour chaque point, accompagné d’au moins une source web fiable par point, en français."
    ),
)

# --------- Helper Functions ---------
def get_tag(content):
    lines = content.strip().split('\n')
    for line in lines:
        tag = line.strip().lower()
        if tag.startswith('#validé') or tag.startswith('#neededresearch') or tag.startswith('#noneededresearch'):
            return tag
    return None

def log_step(step, message):
    print(f"\n=== {step.upper()} ===\n{message[:250]}\n---")

def summarize_knowledge(sources):
    if not sources:
        return "Aucun résultat Google pertinent trouvé."
    joined = "\n\n".join(s[:800] for s in sources)
    prompt = (
        "Voici des extraits issus des 5 premiers résultats Google concernant le sujet de l'article.\n"
        "Fais un résumé structuré et synthétique (max 8 lignes) de ces informations pour alimenter l'article.\n\n"
        + joined
    )
    try:
        summary = writer.generate_reply(messages=[{"role": "user", "content": prompt}])
        return summary if summary else "Résumé non généré."
    except Exception as e:
        return f"Erreur résumé automatique : {e}"

from autogen import GroupChatManager

class StrictWorkflowManager(GroupChatManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_agent = None
        self.validated = False

    def on_message(self, last_message, groupchat):
        """
        Orchestration stricte des rôles pour garantir la séquence éditoriale :
        - Writer → ContentDirector
        - ContentDirector → (Researcher si #neededresearch, Reviewer sinon)
        - Researcher → Writer
        - Reviewer → None (fin)
        """
        role = last_message["role"].lower()
        content = last_message["content"]
        tag = get_tag(content) if role == "contentdirector" else None

        if role == "writer":
            # Toujours passer au ContentDirector après Writer
            return content_director

        elif role == "contentdirector":
            if tag:
                if tag.startswith('#neededresearch'):
                    return researcher
                elif tag.startswith('#validé') or tag.startswith('#noneededresearch'):
                    return reviewer
                else:
                    raise Exception(f"Tag inconnu du ContentDirector : {tag}\nRéponse : {content}")
            else:
                print("Aucun tag trouvé dans la réponse du ContentDirector. Passage automatique au Reviewer.")
                return reviewer

        elif role == "researcher":
            # Recherche terminée : retour au Writer qui doit intégrer la recherche
            return writer

        elif role == "reviewer":
            # Fin du process
            return None

        else:
            raise Exception(f"Rôle d'agent inattendu : {role}")

# --------- MAIN PROCESS ---------
def main():
    topic = input("Quel est le sujet de l'article ? ")
    topic_filename = re.sub(r'[^a-zA-Z0-9_]', '', topic.replace(' ', '_'))

    SERPER_API_KEY = "a4a8a9ef99d85c4102363380cfd7d39a0447ac68"
    external_knowledge = collect_external_knowledge(topic, SERPER_API_KEY)
    summary_snippet = summarize_knowledge(external_knowledge)

    guidelines = f"""Voici les guidelines pour un article sur : {topic}

Résumé des informations issues du web :
{summary_snippet}
"""

    if external_knowledge:
        context_snippet = "\n\n---\nVoici des informations issues des 5 premiers résultats Google :\n"
        for source in external_knowledge:
            context_snippet += "\n" + source[:1000] + "\n..."
        guidelines += context_snippet
    else:
        guidelines += "\n\n---\nAucune information externe n’a pu être récupérée.\n"

    from autogen import GroupChat

    agents = [
        writer,
        content_director,
        researcher,
        reviewer,
    ]
    groupchat = GroupChat(
        agents=agents,
        messages=[],
        max_round=30,
    )
    manager = StrictWorkflowManager(
        groupchat=groupchat,
        llm_config=llm_config,
    )

    # On démarre sur le Writer
    last_agent = writer
    last_content = guidelines
    conversation = []

    # Garde la trace du dernier rôle d'agent pour éviter les auto-boucles
    last_role = None  # Garde la trace du dernier rôle d'agent pour éviter les auto-boucles

    # Boucle principale : gère la passation stricte entre rôles, empêche toute auto-boucle agent-agent
    for _ in range(30):
        current_len = len(groupchat.messages)
        manager.initiate_chat(recipient=last_agent, message=last_content)
        # Wait for a NEW message to be added
        while True:
            if len(groupchat.messages) > current_len:
                break
            time.sleep(0.2)

        # Cherche le dernier message d'un agent "valide" ET différent du rôle précédent
        agent_roles = {"writer", "contentdirector", "reviewer", "researcher"}
        last_message_idx = -1
        force_researcher = False
        force_writer = False
        force_contentdirector = False
        while last_message_idx >= -len(groupchat.messages):
            candidate = groupchat.messages[last_message_idx]
            if candidate['role'].lower() in agent_roles:
                # Ignore si même rôle que le précédent (anti-boucle stricte)
                if last_role is not None and candidate['role'].lower() == last_role:
                    # Si ContentDirector répond 2 fois d'affilée avec #neededresearch, on force le passage au Researcher
                    if candidate['role'].lower() == "contentdirector":
                        tag = get_tag(candidate['content'])
                        if tag and tag.startswith("#neededresearch"):
                            last_message = candidate
                            last_agent = researcher
                            force_researcher = True
                            print("Forçage anti-boucle : ContentDirector ne peut pas répondre 2 fois d'affilée à #neededresearch. Passage forcé au Researcher.")
                            break
                    # Si Researcher répond 2 fois d'affilée, on force le passage au Writer
                    if candidate['role'].lower() == "researcher":
                        last_message = candidate
                        last_agent = writer
                        force_writer = True
                        print("Forçage anti-boucle : Researcher ne peut pas répondre 2 fois d'affilée. Passage forcé au Writer.")
                        break
                    # Si Writer répond 2 fois d'affilée, on force le passage au ContentDirector
                    if candidate['role'].lower() == "writer":
                        last_message = candidate
                        last_agent = content_director
                        force_contentdirector = True
                        print("Forçage anti-boucle : Writer ne peut pas répondre 2 fois d'affilée. Passage forcé au ContentDirector.")
                        break
                    print(f"Boucle détectée : {candidate['role']} vient de répondre deux fois de suite. Arrêt pour éviter une boucle infinie.")
                    final_article = candidate['content']
                    break
                last_message = candidate
                break
            last_message_idx -= 1
        else:
            raise Exception("Aucun message d'agent trouvé dans la pile des messages !")

        role = last_message['role'].lower()
        content = last_message['content']
        conversation.append({"role": role, "content": content})
        log_step(role, content)
        last_content = content

        # Si le rôle est reviewer, on arrête immédiatement le process
        if role == "reviewer":
            final_article = content
            # FORÇAGE : Stoppe immédiatement le workflow après le reviewer (aucun nouvel agent ne doit intervenir)
            # Blocage strict : s'assurer qu'aucun agent n'est appelé après la review finale
            break

        # Si forçage, next_agent déjà fixé
        if force_researcher and role == "contentdirector":
            next_agent = researcher
        elif force_writer and role == "researcher":
            next_agent = writer
        elif force_contentdirector and role == "writer":
            next_agent = content_director
        else:
            next_agent = manager.on_message(last_message, groupchat)
        if next_agent is None:
            final_article = content
            break
        # Anti-boucle : si le prochain agent est le même que l’actuel, on stoppe proprement
        if next_agent.name.lower() == role:
            print(f"Le prochain agent ({next_agent.name}) est identique à celui qui vient de répondre ({role}). Fin de la boucle pour éviter une boucle infinie.")
            final_article = content
            break
        last_agent = next_agent
        last_role = role  # Mémorise ce rôle pour la prochaine boucle

    # Workflow stoppé dès la réponse du Reviewer, aucun passage supplémentaire, pour garantir la terminaison stricte du process éditorial.

    os.makedirs("output", exist_ok=True)
    output_path = f"output/{topic_filename}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_article)
    print(f"\nArticle sauvegardé dans {output_path}")

    print("\n==== CONVERSATION ====")
    for m in conversation:
        short = m['content'][:150].replace('\n',' ') + ("..." if len(m['content']) > 150 else "")
        print(f">> {m['role']} : {short}")

if __name__ == "__main__":
    main()