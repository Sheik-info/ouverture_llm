# FILE CREATION
import json
from pathlib import Path

def getRandomIds(driver : neo4j.Driver, database : str, limit : int) -> list :
    """
    Get random relationship ids from given database.
    """
    try : 
        records, summary, keys = driver.execute_query(f"""
            MATCH p=(n1)-[r]-(n2) 
            WHERE elementId(n1) < elementId(n2)
            RETURN elementId(r), rand() as rand ORDER BY rand LIMIT {limit};
            """,
            database_ = database,
        )
        
        rand_ids = []

        for record in records:  
            rand_ids.append(record.data()["elementId(r)"])

        return rand_ids

    except Exception as error : 
        print(error)


def getGraphFromIds(driver : neo4j.Driver, database : str, limit : int, random_ids : list) -> dict : 
    """
    Get relationships and their associated nodes from database. 
    """
    try : 
        records, summary, keys = driver.execute_query(f"""
            WITH {random_ids} as ids
            MATCH p=(n1)-[r]-(n2) 
            WHERE elementId(n1) < elementId(n2) and elementId(r) in ids
            RETURN p LIMIT {limit};
            """,
            database_ = database,
        )

        graph = {}

        # Loop through results and do something with them
        for record, i in zip(records, range(len(records))):  
            graph[i] = record.data()

        return graph

    except Exception as error : 
        print(error)


def createGraphFile(driver : neo4j.Driver, database : str, limit : int, file_path : str, rewrite : bool = False) :
    if not rewrite :
        if Path(file_path).is_file() : 
            with open(file_path, "r") as file:
                first_char = file.read(1)
                if first_char : 
                    raise ValueError("File already exists and is not empty.")

    rand_ids = getRandomIds(driver, database, limit)
    graph = getGraphFromIds(driver, database, limit, rand_ids)

    with open(file_path, "w") as file:
        json.dump(graph, file)


def getGraphFromFile(file_path : str) -> list : 
    graph = {}
    with open(file_path) as file:
        graph = json.load(file)

    records = []
    for record in graph.keys() : 
        records.append(graph[record])

    return records