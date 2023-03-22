import networkx as nx

import argparse
from datetime import datetime

from map_detection.detectors import *


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
    parser.add_argument('--endpoint_threshold', '-e', type=int,
                        required=False, default=2, help="Minimum count of "
                                                        "consecutive calls "
                                                        "necessary to make a "
                                                        "bundle on endpoint "
                                                        "level detection")
    parser.add_argument('--service_threshold', '-s', type=int,
                        required=False, default=2, help="Minimum count of "
                                                        "consecutive calls "
                                                        "necessary to make a "
                                                        "bundle on service "
                                                        "level detection")
    args = parser.parse_args()
    G = nx.read_edgelist(args.edgelist, create_using=nx.MultiDiGraph, data=[(
        'key', str), ('time', datetime.fromisoformat)])
    frontend_integration(G, frontend_services=set(args.frontends),
                         user=args.user)
    information_holder_resource(G, database_services=set(args.databases),
                                user=args.user)
    request_bundle(args.edgelist, args.service_threshold,
                   args.endpoint_threshold, args.user)
