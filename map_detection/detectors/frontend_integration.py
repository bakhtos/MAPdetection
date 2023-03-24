import networkx as nx

import argparse

from map_detection.read_edgelist import read_edgelist


def frontend_integration(G, frontend_services=None, user='NoUser'):
    """Detect the Frontend Integration API pattern.

    Frontend services should only have outgoing calls. Two things can be done -
    services having only outgoing calls can be considered potential front-end
    services, as well as a given set of frontend services can be checked to
    fulfill this pattern.

    Parameters
    __________
    G : networkx.MultiDiGraph,
        Graph to be studied (converted to simple DiGraph)
    frontend_services : set[str], optional (default None)
        If given, check that services in this set fulfill the property,
        violating services will be returned in frontend_violators
    user : str, optional (default 'NoUser')
        User's name to put in logs

    Returns
    _______
    frontend_candidates : set[str],
        Services that have only outgoing calls.
    frontend_violators : set[str],
        Services from frontend_services that violate the pattern (receive calls)
    """

    if frontend_services is None: frontend_services = set()
    if user is None: user = "NoUser"

    D = nx.DiGraph(G)

    frontend_candidates = set()
    frontend_violators = set()

    for node, in_degree in D.in_degree():
        if in_degree == 0:
            if D.out_degree(node) > 0:
                frontend_candidates.add(node)
                print(f"{user}: Frontend Integration - potential frontend "
                      f" service '{node}' found.")
        elif node in frontend_services:
            frontend_violators.add(node)
            print(f"{user}: Frontend Integration Violation - service '{node}' "
                  f"is designated as frontend service but has incoming calls "
                  f"({in_degree=})")

    return frontend_candidates, frontend_violators


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
    args = parser.parse_args()

    G = read_edgelist(args.edgelist)
    frontends = None if args.frontends is None else set(args.frontends)
    frontend_integration(G, frontend_services=frontends, user=args.user)
