import networkx as nx

import argparse

from map_detection.detectors import *

__all__ = ['read_edgelist']


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--edgelist', '-e', required=True, help="Path to the "
                                                                "graph "
                                                                "edgelist")
    parser.add_argument('--user', '-u', required=False, default='NoUser',
                        help="Name of the User for the logs")
    parser.add_argument('--frontends', '-f', nargs='+', help='List of the '
                                                             'frontend '
                                                             'microservices')
    parser.add_argument('--databases', '-d', nargs='+', help='List of the '
                                                             'database '
                                                             'microservices')
    parser.add_argument('--endpoint_threshold', '-et', type=int,
                        required=False, default=2, help="Minimum count of "
                                                        "consecutive calls "
                                                        "necessary to make a "
                                                        "bundle on endpoint "
                                                        "level detection")
    parser.add_argument('--service_threshold', '-st', type=int,
                        required=False, default=2, help="Minimum count of "
                                                        "consecutive calls "
                                                        "necessary to make a "
                                                        "bundle on service "
                                                        "level detection")
    args = parser.parse_args()
    G = read_edgelist(args.edgelist)
    databases = None if args.databases is None else set(args.databases)
    frontends = None if args.frontends is None else set(args.frontends)
    frontend_integration(G, frontend_services=frontends, user=args.user)
    information_holder_resource(G, database_services=databases, user=args.user)
    request_bundle(args.edgelist, args.service_threshold,
                   args.endpoint_threshold, args.user)
