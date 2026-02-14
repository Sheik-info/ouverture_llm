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

def encode_adjency_from_p_records(records) : 
    graph = "Adjency{\n"
    for record in records : 
        node1 = record["p"][0]
        node2 = record["p"][2]
        
        graph += f"(Node({node1}), Node({node2})),\n\n"
    graph += "}"

    return graph


def encode_edgeList_from_p_records(records) : 
    graph = "EdgeList{\n"
    for record in records : 
        main = record["p"][0]
        graph += f"Node({main}) : "
        edgeList = []
        for record2 in records : 
            node1 = record["p"][0]
            node2 = record["p"][2]

            if (node1 == main and node2 not in edgeList) :
                graph += f"Node({node2}),"
                edgeList.append(node2)
            elif (node2 == main and node1 not in edgeList) :
                graph += f"Node({node1}),"
                edgeList.append(node1)

        
        graph += "\n\n"
    graph += "}"

    return graph


# def extract_graph(records):
#     nodes = {}
#     edges = []

#     for r in records:
#         #MATCH p = ( ... ) RETURN p
#         path = r["p"]
#         for node in path.nodes:
#             #récupère la propriété du noeud
#             nodes[node.id] = dict(node)
#         for rel in path.relationships:
#             edges.append({
#                 #type donné à l'edge :truc
#                 "type": rel.type,
#                 #noeud de départ
#                 "from": rel.start_node.id,
#                 #noeud d'arrivée
#                 "to": rel.end_node.id,
#                 #données interne comme l'importance
#                 "properties": dict(rel)
#             })

#     return nodes, edges


def test(query : str, records : list, option : str = "API"):  

    graph_text_expert = encode_expert_from_p_records(records)
    graph_text_adjency = encode_adjency_from_p_records(records)
    graph_text_edgelist= encode_edgeList_from_p_records(records)
    
    # Prompt avec graphe
    graph_prompt_expert = f"""
    You are given a knowledge graph extracted from Neo4j.

    Question:
    {query}

    Graph:
    {graph_text_expert}

    Answer using only the information in the graph. Be concise.
    """

    graph_prompt_adjency = f"""
    You are given a knowledge graph extracted from Neo4j.

    Question:
    {query}

    Graph:
    {graph_text_adjency}

    Answer using only the information in the graph. Be concise.
    """

    graph_prompt_edgeList = f"""
    You are given a knowledge graph extracted from Neo4j.

    Question:
    {query}

    Graph:
    {graph_text_edgelist}

    Answer using only the information in the graph. Be concise.
    """
    
    print(graph_prompt_expert)
    print("\n\n===================\n\n")
    print(graph_prompt_adjency)
    print("\n\n===================\n\n")
    print(graph_prompt_edgeList)

    #graph_answer = queryLLLM(graph_prompt, option)
    #print("=== LLM answer ===")
    #print(graph_answer)
