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


graphs_tests = {
    "stackoverflow-50" : 
        {
            "file_names" : 
            {
                "stackoverflow_4" : 4,
                #"stackoverflow_12" : 12,
                #"stackoverflow_20" : 20
            },
            "queries" : ["Who has answered multiple times to a question?"]
        },
    "recommendations-5.26" : 
        {
            "file_names" : 
            {
                "recommendations_4" : 4,
                #"recommendations_12" : 12,
                #"recommendations_20" : 20
            },
            "queries" : ["Who has made multiple recommendations?"]
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
    for graph in graphs_tests.keys() :
        file_names = graphs_tests[graph]["file_names"]
        for file in file_names : 
            try : 
                records = con.getGraphFromFile(f"{global_path}/{file}.json")
                
                print(records)

                # TODO : A DECOMMENTER QUAND IA
                for query in graphs_tests[graph]["queries"] : 
                    en.test(query=query, records=records, option=option)

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
    LLM_OPTION = os.getenv("LLM_OPTION")
    GENERATE_GRAPHS = True if os.getenv("GENERATE_GRAPHS") == "TRUE" else False

    try : 
        if GENERATE_GRAPHS : 
            generateGraphsFiles(global_path="graphs") # We save it all in graphs/      
        
        testGraphs(global_path="graphs", option=LLM_OPTION)


    except ClientError as error :
        print("Connection error : " + error.message)

