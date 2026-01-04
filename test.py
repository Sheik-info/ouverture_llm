# test.py
from neo4j import GraphDatabase, basic_auth
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from dotenv import load_dotenv
import time
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
MERGE (s:Serie {name: 'Bing Bang Theory'})

MERGE (a1:Actor {name: 'Jim Parsons'})
SET a1.hair = 'brun'
MERGE (a1)-[:PLAY_IN {character: 'Sheldon Cooper'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'principal'}]->(a1)


MERGE (a2:Actor {name: 'Johnny Galeki'})
SET a2.hair = 'brun'
MERGE (a2)-[:PLAY_IN {character: 'Leonard Hofstadter'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'principal'}]->(a2)


MERGE (a3:Actor {name: 'Kaley Cuoco'})
SET a3.hair = 'blond'
MERGE (a3)-[:PLAY_IN {character: 'Penny'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'secondary'}]->(a3)


MERGE (a4:Actor {name: 'Simon Helberg'})
SET a4.hair = 'brun'
MERGE (a4)-[:PLAY_IN {character: 'Howard Wolowitz'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'secondary'}]->(a4)


MERGE (a5:Actor {name: 'Mayim Bialik'})
SET a5.hair = 'brun'
MERGE (a5)-[:PLAY_IN {character: 'Amy Farrah Fowler'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'secondary'}]->(a5)


MERGE (a6:Actor {name: 'Kunal Nayyar'})
SET a6.hair = 'noir'
MERGE (a6)-[:PLAY_IN {character: 'Rajesh Koothrappali'}]->(s)
MERGE (s)-[:IMPORTANCE {importance: 'tertiary'}]->(a6)

"""



driver = GraphDatabase.driver(
    f"bolt://localhost:{DATABASE_PORT}",
    auth=basic_auth(DATABASE_AUTH, DATABASE_PWD)
)


llm = OpenAILLM(
    #model_name="qwen/qwen-2.5-72b-instruct",          
    # Alternatives qui marchent aussi très bien :
    #model_name="mistralai/mistral-small-24b-instruct-2501",
    model_name="google/gemini-2.0-flash-001",
    api_key="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",
    base_url="https://openrouter.ai/api/v1",
    model_params={"temperature": 0.0}
)

neo4j_shema = """
    Node properties:
    Actor {name: STRING, hair: STRING}
    Serie {name: STRING}
    Relationship properties:
    PLAY_IN {character: STRING}
    IMPORTANCE {importance: STRING}
    The relationships:
    (:Actor)-[:PLAY_IN]->(:Serie)
    (:Serie)-[:IMPORTANCE]->(:Actor)
    
"""

examples = [
    """USER INPUT: "What is Penny hair color?"
QUERY:
MATCH (a:Actor)-[:PLAY_IN {character: 'Penny'}]->(:Serie)
RETURN a.hair"""
]


test_cases = [
    {
        "question": "What is the Sheldon Cooper hair color?",
        "expected": "brun"
    },
    {
        "question": "What is Penny hair color?",
        "expected": "blond"
    }
]


retriever = Text2CypherRetriever(
    driver=driver,
    llm=llm,
    neo4j_schema=neo4j_shema,
    examples=examples,
)


query_text = "What is the Sheldon Cooper hair color?"
print(retriever.search(query_text=query_text))


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



def evaluate_text2cypher(retriever, test_cases):
    results = []

    for test in test_cases:
        question = test["question"]
        expected = test["expected"]

        start_time = time.time()

        response = retriever.search(query_text=question)

        end_time = time.time()

        total_time = end_time - start_time

        # récupération réponse texte
        if response and response.items:
            answer = response.items[0].content
        else:
            answer = None


        correct = expected.lower() in str(answer).lower()

        results.append({
            "question": question,
            "expected": expected,
            "answer": answer,
            "correct": correct,
            "total_time_sec": round(total_time, 3)
        })

    return results


#test avec graphe
results = evaluate_text2cypher(retriever, test_cases)

for r in results:
    print(r)


def extract_text_from_llm_response(resp):
    if hasattr(resp, "text"):
        return resp.text
    return str(resp)



def ask_llm_only(llm, question):
    start_time = time.time()

    response = llm.invoke(question)

    end_time = time.time()

    answer_text = extract_text_from_llm_response(response)

    return {
        "answer": answer_text,
        "time_sec": round(end_time - start_time, 3)
    }



def evaluate_llm_only(llm, test_cases):
    results = []

    for test in test_cases:
        question = test["question"]
        expected = test["expected"]
    
        result = ask_llm_only(llm, question)

        correct = expected.lower() in result["answer"].lower()

        results.append({
            "question": question,
            "expected": expected,
            "answer": result["answer"],
            "correct": correct,
            "time_sec": result["time_sec"]
        })

    return results


#pour le test sans graphe
# results = evaluate_llm_only(llm,test_cases)

# for r in results:
#     print(r)


# def test():  
#     query = "who play Leonard in big bang theory?"
#     print("Question :", query)

#     result = retriever.get_search_results(query)  

#     generated_cypher = result.metadata.get("generated_cypher", "Inconnu (pas dans metadata)")
#     print("\nCypher généré par le retriever\n")

#     records = result.records  

#     if not records:
#         print("Aucun résultat retourné par la requête Cypher.")
#         return

#     nodes, edges = extract_graph(records)
#     print(nodes)
#     graph_text = encode_graph_text(nodes, edges)

#     print("\n=== Sous-graphe encodé ===\n")
#     print(graph_text)

#     # Prompt avec graphe
#     graph_prompt = f"""
# You are given a knowledge graph extracted from Neo4j.

# Graph:
# {graph_text}

# Question:
# {query}

# Answer using only the information in the graph. Be concise.
# """

#     graph_answer = asyncio.run(llm.acall(graph_prompt))
#     print("\n=== Réponse AVEC graphe ===\n")
#     print(graph_answer.content if hasattr(graph_answer, "content") else graph_answer)

#     # 5) Baseline
#     baseline_prompt = f"Answer the question concisely:\n{query}"
#     baseline_answer = asyncio.run(llm.acall(baseline_prompt))
#     print("\n=== Réponse SANS graphe ===\n")
#     print(baseline_answer.content if hasattr(baseline_answer, "content") else baseline_answer)


# if __name__ == "__main__":
#     with driver.session() as session:
#         session.run(graph_use)
#         print("Graphe injecté dans Neo4j !")
#     test() 
#     driver.close()
#     print("\nFin du script – tout s'est bien passé !")



## Démarrer le conteneur
#podman start neo4j-apoc

# Redémarrer le conteneur
#podman restart neo4j-apoc

#podman stop neo4j-apoc

#neo4j
