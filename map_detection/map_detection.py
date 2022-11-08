import networkx as nx

from map_detection.utils import *

__all__ = ['generate_call_graphs']


def generate_call_graphs(pptam_dir, tracing_dir, time_delta):
    user_boundaries, instance_boundaries = detect_users(pptam_dir, time_delta)

    # Get calls and pipelines for each user using logs of each service
    pipelines, call_counters = parse_logs(tracing_dir, user_boundaries,
                                          instance_boundaries)

    # Create networkx' multigraph, edges are identified by User
    user_graphs = dict()
    for user, counter in call_counters.items():
        G = nx.MultiDiGraph()
        user_graphs[user] = G
        for keys, weight in counter.items():
            G.add_edge(keys[0], keys[1], key=keys[2], weight=weight)

    return user_graphs, pipelines
