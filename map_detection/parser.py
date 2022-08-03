import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import os
import json
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


if __name__ == '__main__':
    
    directory = "kubernetes-istio-sleuth-v0.2.1-separate-load"
    pptam_dir = os.path.join(directory, 'pptam')
    tracing_dir = os.path.join(directory, 'tracing-log')
    time_delta = timedelta(hours=-8)
    G, pipelines = generate_call_graph(pptam_dir, tracing_dir, time_delta)
    bundles_service, bundles_endpoint = detect_request_bundle(pipelines)
    #write_pipelines(pipelines)
    #draw_graph(G, intervals)

