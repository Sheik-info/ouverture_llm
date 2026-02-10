import time


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
