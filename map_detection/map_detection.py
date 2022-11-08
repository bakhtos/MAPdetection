import networkx as nx

from map_detection.utils import *

__all__ = ['generate_call_graphs']


def generate_call_graphs(pptam_dir, tracing_dir, time_delta):
    """Create call graphs and pipelines based on logs location.

    Parameters
    __________
    pptam_dir - str,
        Directory storing directories with pptam/locust configurations and
        logs for each user (will be passed to detect_users()).
    tracing_dir - str,
        Directory containing tracing logs for each microservice (will be
        passed to parse_logs()).
    time_delta - datetime.timedelta,
        Corrective timedelta to add to all timestamps in locust log (will be
        passed to detect_users()).

    Returns
    _______
    user_graphs : dict[str] -> networkx.MultiDiGraph,
        For each user[_instance], a multigraph where nodes are services and
        edges are calls between services keyed by the endpoint.
    pipelines : dict[str] -> list[tuple[datetime, str, str, str]],
        For each user[_instance], list of tuples containing the datetime of
        the call, calling service, called service and called endpoint,
        sorted by the time of call.
    """
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
