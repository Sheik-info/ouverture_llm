# test.py
from neo4j import GraphDatabase, basic_auth
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from dotenv import load_dotenv
import asyncio
import nest_asyncio
import os

# Permet d'utiliser asyncio.run() même dans Jupyter ou quand un loop existe déjà
nest_asyncio.apply()

# Load environment variables
load_dotenv()
DATABASE_AUTH = os.getenv("DATABASE_AUTH")
DATABASE_PWD = os.getenv("DATABASE_PWD")
DATABASE_PORT = os.getenv("DATABASE_PORT")



graph_use ="""
MERGE (s:Serie {nom: 'Bing Bang Theory'})

MERGE (a1:Acteur {nom: 'Jim Parsons'})
SET a1.cheveux = 'brun'
MERGE (a1)-[:JOUE_DANS {role: 'Sheldon Cooper'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'principale'}]->(a1)


MERGE (a2:Acteur {nom: 'Johnny Galeki'})
SET a2.cheveux = 'brun'
MERGE (a2)-[:JOUE_DANS {role: 'Leonard Hofstadter'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'principale'}]->(a2)


MERGE (a3:Acteur {nom: 'Kaley Cuoco'})
SET a3.cheveux = 'blond'
MERGE (a3)-[:JOUE_DANS {role: 'Penny'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'secondaire'}]->(a3)


MERGE (a4:Acteur {nom: 'Simon Helberg'})
SET a4.cheveux = 'brun'
MERGE (a4)-[:JOUE_DANS {role: 'Howard Wolowitz'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'secondaire'}]->(a4)


MERGE (a5:Acteur {nom: 'Mayim Bialik'})
SET a5.cheveux = 'brun'
MERGE (a5)-[:JOUE_DANS {role: 'Amy Farrah Fowler'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'secondaire'}]->(a5)


MERGE (a6:Acteur {nom: 'Kunal Nayyar'})
SET a6.cheveux = 'noir'
MERGE (a6)-[:JOUE_DANS {role: 'Rajesh Koothrappali'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'terciaire'}]->(a6)

"""



driver = GraphDatabase.driver(
    f"bolt://localhost:{DATABASE_PORT}",
    auth=basic_auth(DATABASE_AUTH, DATABASE_PWD)
)


llm = OpenAILLM(
    model_name="qwen/qwen-2.5-72b-instruct",          
    # Alternatives qui marchent aussi très bien :
    # "mistralai/mistral-small-24b-instruct"
    # "google/gemini-flash-1.5-exp"
    api_key="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",
    base_url="https://openrouter.ai/api/v1",
    model_params={"temperature": 0.0}
)


retriever = Text2CypherRetriever(driver=driver, llm=llm)


def extract_graph(records):
    nodes = {}
    edges = []

    for r in records:
        #MATCH p = ( ... ) RETURN p
        path = r["p"]
        for node in path.nodes:
            #récupère la propriété du noeud
            nodes[node.id] = dict(node)
        for rel in path.relationships:
            edges.append({
                #type donné à l'edge :truc
                "type": rel.type,
                #noeud de départ
                "from": rel.start_node.id,
                #noeud d'arrivée
                "to": rel.end_node.id,
                #données interne comme l'importance
                "properties": dict(rel)
            })

    return nodes, edges


#on encode pour que ça soit compréhensible pour le llm
def encode_graph_text(nodes, edges):
    #une ligne par relation 
    #noeud -> edge -> noeud
    lines = []

    for edge in edges:
        #on récupère la source et la destination pour chanque noeud
        src = nodes[edge["from"]]
        dst = nodes[edge["to"]]

        #j'aurais du mettre name au lieu de nom ici mais pas grâve
        src_name = src.get("nom", "Unknown")
        dst_name = dst.get("nom", "Unknown")

        line = f"{src_name} --{edge['type']}--> {dst_name}"
        if edge["properties"]:
            line += f" {edge['properties']}"
        lines.append(line)

    return "\n".join(lines)



def test():  
    query = "who is the main character in big bang theory"
    print("Question :", query)

    # 1) Génération + exécution du Cypher (tout-en-un)
    result = retriever.get_search_results(query)  

    # Récupère le Cypher généré depuis les metadata
    generated_cypher = result.metadata.get("generated_cypher", "Inconnu (pas dans metadata)")
    print("\n=== Cypher généré ===\n")
    print(generated_cypher)

    # 2) Les records sont déjà exécutés et disponibles !
    records = result.records  # ← Directement ici, pas besoin de re-exécuter

    if not records:
        print("Aucun résultat retourné par la requête Cypher.")
        return

    # 3) Extraction du graphe (je garde une version robuste améliorée)
    nodes, edges = extract_graph(records)
    graph_text = encode_graph_text(nodes, edges)

    print("\n=== Sous-graphe encodé ===\n")
    print(graph_text)

    # 4) Prompt avec graphe
    graph_prompt = f"""
You are given a knowledge graph extracted from Neo4j.

Graph:
{graph_text}

Question:
{query}

Answer using only the information in the graph. Be concise.
"""

    graph_answer = asyncio.run(llm.acall(graph_prompt))
    print("\n=== Réponse AVEC graphe ===\n")
    print(graph_answer.content if hasattr(graph_answer, "content") else graph_answer)

    # 5) Baseline
    baseline_prompt = f"Answer the question concisely:\n{query}"
    baseline_answer = asyncio.run(llm.acall(baseline_prompt))
    print("\n=== Réponse SANS graphe ===\n")
    print(baseline_answer.content if hasattr(baseline_answer, "content") else baseline_answer)

if __name__ == "__main__":
    print("Connexion en cours avec user:", DATABASE_AUTH)
    test() 
    driver.close()
    print("\nFin du script – tout s'est bien passé !")



## Démarrer le conteneur
#podman start neo4j-apoc

# Redémarrer le conteneur
#podman restart neo4j-apoc

#podman stop neo4j-apoc

#neo4j
