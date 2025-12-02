# test.py
from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from dotenv import load_dotenv
import asyncio
import nest_asyncio
import os

# Permet d'utiliser asyncio.run() même dans Jupyter ou quand un loop existe déjà
nest_asyncio.apply()

#connection à neo4j
driver = GraphDatabase.driver(f"bolt://localhost:{DATABASE_PORT}", auth=(DATABASE_AUTH, DATABASE_PWD))


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


def encode(edges):
    nodes = {}
    
    return


async def test():
    query = "What is the tallest animal on earth"
    print("Question :", query)
    
    result = await retriever.get_search_results(query)
    
    print("\n=== Cypher généré ===\n")
    print(result.query_text)
    
    # Exécution du Cypher généré
    try:
        with driver.session() as session:
            records = session.run(result.query_text).data()
            print("\n=== Résultat Neo4j ===")
            if records:
                for r in records:
                    print(r)
            else:
                print("→ Aucun résultat (ta base est vide ou le Cypher ne trouve rien → normal pour ce test)")
    except Exception as e:
        print("Erreur lors de l'exécution du Cypher :", e)

#lancement
if __name__ == "__main__":

    load_dotenv()
    DATABASE_AUTH = os.getenv("DATABASE_AUTH")
    DATABASE_PWD = os.getenv("DATABASE_PWD")
    DATABASE_PORT = os.getenv("DATABASE_PORT")

    print(DATABASE_AUTH, DATABASE_PWD, DATABASE_AUTH)

    asyncio.run(test())
    driver.close()
    print("\nFin du script – tout s'est bien passé !")

## Démarrer le conteneur
#podman start neo4j-apoc

# Redémarrer le conteneur
#podman restart neo4j-apoc

#podman stop neo4j-apoc

#neo4j
