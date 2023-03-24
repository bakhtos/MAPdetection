import networkx as nx


def read_edgelist(path):
    G = nx.MultiDiGraph()
    with open(path, 'r') as f:
        edges = f.readlines()
    for edge in edges:
        parts = edge.split(' ')
        from_ = parts[0]
        to_ = parts[1]
        key_ = parts[2]
        if (from_, to_, key_) in G.edges:
            G.edges[from_, to_, key_]["weight"] += 1
        else:
            G.add_edge(from_, to_, key_, weight=1)

    return G
