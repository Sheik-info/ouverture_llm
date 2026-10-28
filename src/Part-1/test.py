# test.py
from neo4j import GraphDatabase, basic_auth
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from dotenv import load_dotenv
from eval import *
from encode import *
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
    #Alternatives qui marchent aussi très bien :
    model_name="qwen/qwen-2.5-72b-instruct",          
    #model_name="mistralai/mistral-small-24b-instruct-2501",
    #model_name="google/gemini-2.0-flash-001",
    api_key="clé api que tu veux",
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




with driver.session() as session:
    records = session.run(GRAPH_QUERY)

    nodes, edges = extract_graph(records)
    graph_text = encode_graph_incidence(nodes, edges)

    results = eval_global_llm(llm, graph_text, test_cases)

    for r in results:
        print(r)

driver.close()


