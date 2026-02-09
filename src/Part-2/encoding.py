# ENV VARIABLES
from dotenv import load_dotenv
import os
# NEO4J
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
import nest_asyncio
# TESTS
import time

# Permet d'utiliser asyncio.run() même dans Jupyter ou quand un loop existe déjà
nest_asyncio.apply()


#---------------------------------------------------------------------------------
#-------------------------------- LLMs
#---------------------------------------------------------------------------------


def queryOllama(prompt : str) -> str:
    from ollama import chat, ChatResponse
    
    response: ChatResponse = chat(model='llama3.2:3b', messages=[
    {
        'role': 'user',
        'content': prompt,
    },
    ])
    return response.message.content


def getOpenAiLLM() :
    load_dotenv()
    OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY")

    return OpenAILLM(
        model_name="qwen/qwen-2.5-72b-instruct",          
        # Alternatives qui marchent aussi très bien :
        #model_name="mistralai/mistral-small-24b-instruct-2501",
        #model_name="google/gemini-2.0-flash-001",
        #api_key=OPEN_ROUTER_KEY,
        #base_url="https://openrouter.ai/api/v1",
        api_key="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",
        model_params={"temperature": 0.0}
    )


def queryOpenAiLLM(prompt : str) -> str: 
    llm = getOpenAiLLM()
    return asyncio.run(llm.acall(prompt))


def queryLLLM(prompt : str, option : str = "API") -> str: 
    """
    Returns the appropriate LLM generated response from prompt.
    """
    if option == "API" : 
        return queryOpenAiLLM(prompt)
    elif option == "LOCAL" : 
        return queryOllama(prompt)
    else :
        raise ValueError("Option of LLM isn't defined.")



def ask_llm_only(llm, question):
    start_time = time.time()

    response = llm.invoke(question)

    end_time = time.time()

    answer_text = extract_text_from_llm_response(response)

    return {
        "answer": answer_text,
        "time_sec": round(end_time - start_time, 3)
    }


#---------------------------------------------------------------------------------
#-------------------------------- ENCODING
#---------------------------------------------------------------------------------


def encode_expert_from_p_records(records) :
    graph = ""
    for record in records : 
        #print(record)
        node1 = record["p"][0]
        relation = record["p"][1]
        node2 = record["p"][2]
        
        graph += f"Node({node1}) <== {relation} ==> Node({node2})\n\n"

    return graph


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


def extract_text_from_llm_response(resp):
    if hasattr(resp, "text"):
        return resp.text
    return str(resp)


#---------------------------------------------------------------------------------
#-------------------------------- EVALUATION
#---------------------------------------------------------------------------------


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


def test(query : str, records : list, option : str = "API"):  

    graph_text = encode_expert_from_p_records(records)

    print("\n=== Encoded Graph ===\n")
    
    print(graph_text)

    # Prompt avec graphe
    graph_prompt = f"""
    You are given a knowledge graph extracted from Neo4j.

    Question:
    {query}

    Graph:
    {graph_text}

    Answer using only the information in the graph. Be concise.
    """

    graph_answer = queryLLLM(graph_prompt, option)

    print("=== LLM answer ===")
