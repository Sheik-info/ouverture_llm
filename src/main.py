# ENV VARIABLES
from dotenv import load_dotenv
import os
import ast
# NEO4J
import neo4jConnection as con
from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ClientError
# LLM
import encoding as en

#---------------------------------------------------------------------------------
#-------------------------------- GLOBAL VARIABLES
#---------------------------------------------------------------------------------


databases_graphs = [
    "neo4j",
    "stackoverflow-50", 
    "recommendations-5.26"
]

graphs_tests = {
    "stackoverflow-50" : 
        {
            "file_names" : 
            {
                "stackoverflow_4" : 4,
                "stackoverflow_12" : 12,
                #"stackoverflow_20" : 20
            },
            "queries" : []
        },
    "recommendations-5.26" : 
        {
            "file_names" : 
            {
                "recommendations_4" : 4,
                "recommendations_12" : 12,
                #"recommendations_20" : 20
            },
            "queries" : []
        }
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
    for graph in graphs_tests.keys() :
        file_names = graphs_tests[graph]["file_names"]
        for file in file_names : 
            try : 
                con.createGraphFile(
                    driver=driver, 
                    database=databases_graphs[1], 
                    limit=file_names[file], 
                    file_path=f"{global_path}/{file}.json", 
                    rewrite=rewrite
                )
            except ValueError as error :
                print(error)


def testGraphs(global_path : str) :
    for graph in graphs_tests.keys() :
        file_names = graphs_tests[graph]["file_names"]
        for file in file_names : 
            try : 
                records = con.getGraphFromFile(f"{global_path}/{file}.json")
                
                print(records)

                # TODO : A DECOMMENTER QUAND IA
                # for query in graph["queries"] : 
                #     en.test(query=query, records=records)

            except ValueError as error :
                print(error)       

#---------------------------------------------------------------------------------
#-------------------------------- MAIN PROGRAM
#---------------------------------------------------------------------------------


if __name__ == "__main__" : 
    
    load_dotenv()
    DATABASE_AUTH = os.getenv("DATABASE_AUTH")
    DATABASE_PWD = os.getenv("DATABASE_PWD")
    DATABASE_HOST = os.getenv("DATABASE_HOST")
    
    try : 
        driver = GraphDatabase.driver(
            DATABASE_HOST,
            auth=basic_auth(DATABASE_AUTH, DATABASE_PWD)
        )

        global_path="graphs"
        generateGraphsFiles(global_path=global_path) # We save it all in graphs/      
        testGraphs(global_path=global_path)

        driver.close()

    except ClientError as error :
        print("Connection error : " + error.message)

