# ENV VARIABLES
from dotenv import load_dotenv
import os
# NEO4J
import neo4jConnection as con
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ClientError
# LLM
import encoding as en

#---------------------------------------------------------------------------------
#-------------------------------- GLOBAL VARIABLES
#---------------------------------------------------------------------------------

test_graph = """
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


graphs_tests = {
    "stackoverflow-50" : 
        {
            "file_names" : 
            {
                "stackoverflow_3" : 4,
                "stackoverflow_6" : 7,
                #"stackoverflow_20" : 20
            },
            "queries" : ["What is the general subject of the questions?"]
        },
    "recommendations-5.26" : 
        {
            "file_names" : 
            {
                #"recommendations_4" : 4,
                #"recommendations_12" : 12,
                #"recommendations_20" : 20
            },
            "queries" : ["Who has made multiple recommendations?"]
        },
    "northwind-50" : 
        {
            "file_names" : 
            {
                "northwind-3" : 4,
                "northwind-6" : 7
            },
            "queries" : ["What is the mean quantity of commands?"]

        },
    "pole-50" : 
        {
            "file_names" : 
            {
                "pole-3" : 4,
                "pole-6" : 7
            },
            "queries" : ["Can you tell me which is the most common crime?"]

        },

}


#---------------------------------------------------------------------------------
#-------------------------------- GLOBAL FUNCTIONS
#---------------------------------------------------------------------------------

def generateGraphsFiles(global_path : str, rewrite : bool = False) :
    """
    Generate files containing a certain number of random relationship elements from
    given databases. 
    
    Parameters
    ----------
    global_path
        Files are all stored in global_path

    """
    driver = GraphDatabase.driver(
            DATABASE_HOST,
            auth=basic_auth(DATABASE_AUTH, DATABASE_PWD)
        )

    for graph in graphs_tests.keys() :
        file_names = graphs_tests[graph]["file_names"]
        for file in file_names : 
            try : 
                con.createGraphFile(
                    driver=driver, 
                    database=graph, 
                    limit=file_names[file], 
                    file_path=f"{global_path}/{file}.json", 
                    rewrite=rewrite
                )
            except ValueError as error :
                print(error)
            except Exception as error :
                print("An error occured : ", error)
                generateGraphsFiles(global_path, rewrite) #we retry until we have all files 
    
    driver.close()


def testGraphs(global_path : str, option : str) :

    if TEST_GRAPH : 
        driver = GraphDatabase.driver(
            DATABASE_HOST,
            auth=basic_auth(DATABASE_AUTH, DATABASE_PWD),
            database=TEST_GRAPH_DB
        )
        en.testGraph(driver, test_graph)
        driver.close()

    for graph in graphs_tests.keys() :
        file_names = graphs_tests[graph]["file_names"]
        for file in file_names : 
            try : 
                records = con.getGraphFromFile(f"{global_path}/{file}.json")
                
                #print(records)

                print(f"\n\n======== OUTPUTS FOR {file} =========\n\n")

                # TODO : A DECOMMENTER QUAND IA
                for query in graphs_tests[graph]["queries"] : 
                    en.test(query=query, records=records, option=option)

            except ValueError as error :
                print(error)       
                

def addTestGraph(test_graph : str, database : str) : 
    driver = GraphDatabase.driver(
        DATABASE_HOST,
        auth=basic_auth(DATABASE_AUTH, DATABASE_PWD),
        database=database
    )

    with driver.session() as session:
        session.run(test_graph)
        print(f"Graphe injecté dans Neo4j sur la base {database} !")

    driver.close()

#---------------------------------------------------------------------------------
#-------------------------------- MAIN PROGRAM
#---------------------------------------------------------------------------------


if __name__ == "__main__" : 
    
    load_dotenv()
    DATABASE_AUTH = os.getenv("DATABASE_AUTH")
    DATABASE_PWD = os.getenv("DATABASE_PWD")
    DATABASE_HOST = os.getenv("DATABASE_HOST")
    LLM_OPTION = os.getenv("LLM_OPTION") if os.getenv("LLM_OPTION") != None else "API" # LOCAL or API
    GENERATE_GRAPHS = True if os.getenv("GENERATE_GRAPHS") == "TRUE" else False # TRUE or FALSE
    TEST_GRAPH = True if os.getenv("TEST_GRAPH") == True else False
    TEST_GRAPH_DB = os.getenv("TEST_GRAPH_DB") if (os.getenv("TEST_GRAPH") and os.getenv("TEST_GRAPH_DB")) else False

    try : 
        if GENERATE_GRAPHS : 
            generateGraphsFiles(global_path="graphs") # We save it all in graphs/      
        
        if TEST_GRAPH : 
            addTestGraph(test_graph, TEST_GRAPH_DB)

        print("\n=== Graphs LLM test ===\n")
        testGraphs(global_path="graphs", option=LLM_OPTION)


    except ClientError as error :
        print("Connection error : " + error.message)

