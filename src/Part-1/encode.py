


def encode_graph_expert(nodes, edges):
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



def encode_graph_adjacency(nodes, edges):
    edge_set = set()

    for edge in edges:
        src = nodes[edge["from"]].get("name", edge["from"])
        dst = nodes[edge["to"]].get("name", edge["to"])

        edge_set.add(tuple(sorted((src, dst))))

    pairs = ", ".join(f"({a}, {b})" for a, b in sorted(edge_set))

    return f"Adjacency:\n{pairs}"


def encode_graph_incidence(nodes, edges):
    node_ids = list(nodes.keys())
    index = {node_id: i for i, node_id in enumerate(node_ids)}

    adjacency = {index[node_id]: set() for node_id in node_ids}

    for edge in edges:
        src = index[edge["from"]]
        dst = index[edge["to"]]

        adjacency[src].add(dst)
        adjacency[dst].add(src)

    lines = ["Incident:"]
    for node, neighbors in adjacency.items():
        neighbors_str = ", ".join(str(n) for n in sorted(neighbors))
        lines.append(f"Node {node}: {neighbors_str}")

    return "\n".join(lines)
