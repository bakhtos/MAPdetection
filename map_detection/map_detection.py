import networkx as nx

import os
from collections import Counter
from datetime import datetime, timedelta


def generate_call_graph(pptam_dir, tracing_dir, time_delta):
    user_boundaries, instance_boundaries = detect_users(pptam_dir, time_delta)

    # Get calls and pipelines for each user using logs of each service
    call_counters = dict()
    pipelines = dict()
    for file in os.listdir(tracing_dir):
        if file.endswith(".log"):
            parse_logs(tracing_dir, file, user_boundaries, instance_boundaries, call_counters, pipelines)

    # Sort pipelines by time of call
    for l in pipelines.values():
        l.sort(key = lambda x: x[0])

    # Create networkx' multigraph, edges are identified by User
    user_graphs = dict()
    for user, counter in call_counters.items():
        G = nx.MultiDiGraph()
        user_graphs[user] = G
        for keys, weight in counter.items():
            G.add_edge(keys[0], keys[1], key=keys[2], weight=weight)

    return user_graphs, pipelines
