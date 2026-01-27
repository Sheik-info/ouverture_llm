# test.py
from neo4j import GraphDatabase, basic_auth
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

GRAPH_QUERY = """
MATCH p = (a:Actor)-[r]->(s:Serie)
RETURN p
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


QUESTION = "Who play Penny in big bang theory?"



query_text = "What is the Sheldon Cooper hair color?"
#print(retriever.search(query_text=query_text))


test_cases = [
    {
        "question": "Who play Penny in big bang theory?",
        "expected": "Kaley Cuoco"
    },
    {
        "question": "Who play Sheldon Cooper?",
        "expected": "Jim Parsons"
    },
    {
        "question": "Who play Rajesh Koothrappali?",
        "expected": "Kunal Nayyar"
    }
]


def extract_graph(records):
    nodes = {}
    edges = []

    for r in records:
        path = r["p"]

        for node in path.nodes:
            nodes[node.element_id] = dict(node)

        for rel in path.relationships:
            edges.append({
                "type": rel.type,
                "from": rel.start_node.element_id,
                "to": rel.end_node.element_id,
                "properties": dict(rel)
            })

    return nodes, edges


def encode_graph_text(nodes, edges):
    lines = []

    for edge in edges:
        src = nodes[edge["from"]]
        dst = nodes[edge["to"]]

        src_name = src.get("name", "Unknown")
        dst_name = dst.get("name", "Unknown")

        line = f"{src_name} --{edge['type']}--> {dst_name}"
        if edge["properties"]:
            line += f" {edge['properties']}"

        lines.append(line)

    return "\n".join(lines)





def evaluate_llm_without_graph(llm, test_cases):
    results = []

    for test in test_cases:
        question = test["question"]
        expected = test["expected"]

        start = time.time()
        response = llm.invoke(question)

        if hasattr(response, "content"):
            answer = response.content
        elif hasattr(response, "message"):
            answer = response.message
        elif hasattr(response, "choices"):
            answer = response.choices[0].message.content
        else:
            answer = str(response)

        elapsed = round(time.time() - start, 3)
        correct = expected.lower() in answer.lower()

        results.append({
            "mode": "llm_only",
            "question": question,
            "expected": expected,
            "answer": answer,
            "correct": correct,
            "time_sec": elapsed
        })

    return results


def evaluate_llm_with_graph(llm, graph_text, test_cases):
    results = []

    for test in test_cases:
        question = test["question"]
        expected = test["expected"]

        prompt = f"""
You are given a graph extracted from a Neo4j database.

Graph:
{graph_text}

Question:
{question}

Answer using only the information in the graph.
Be concise and precise.
"""

        start = time.time()
        response = llm.invoke(prompt)

        if hasattr(response, "content"):
            answer = response.content
        elif hasattr(response, "message"):
            answer = response.message
        elif hasattr(response, "choices"):
            answer = response.choices[0].message.content
        else:
            answer = str(response)

        elapsed = round(time.time() - start, 3)
        correct = expected.lower() in answer.lower()

        results.append({
            "mode": "llm_with_graph",
            "question": question,
            "expected": expected,
            "answer": answer,
            "correct": correct,
            "time_sec": elapsed
        })

    return results


def eval_global_llm(llm, graph_text, test_cases):
    results = []

    results.extend(evaluate_llm_without_graph(llm, test_cases))
    results.extend(evaluate_llm_with_graph(llm, graph_text, test_cases))

    return results




with driver.session() as session:
    records = session.run(GRAPH_QUERY)

    nodes, edges = extract_graph(records)
    graph_text = encode_graph_text(nodes, edges)

    results = eval_global_llm(llm, graph_text, test_cases)

    for r in results:
        print(r)

driver.close()




## Démarrer le conteneur
#podman start neo4j-apoc

# Redémarrer le conteneur
#podman restart neo4j-apoc

#podman stop neo4j-apoc

#neo4j
