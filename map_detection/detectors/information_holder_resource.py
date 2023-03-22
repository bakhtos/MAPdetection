import networkx as nx


def detect_information_holder_resource(G, database_services=None,
                                       user='NoUser'):
    """Detect the Information Holder Resource pattern.

    Information Holder Resource (IHR) and Database (DB) service pairs are such
    that a DB service is only called from IHR and IHR only calls DB.

    Parameters
    __________
    G : networkx.MultiDiGraph,
        Graph to be studied (converted to simple DiGraph)
    database_services : set[str], optional (default None)
        If given, check that services in this set fulfill the property,
        violating services will be returned in database_call_violators and
        database_no_ihr_violators
    user : str, optional (default 'NoUser')
        User's name to put in logs

    Returns
    _______
    ihr_candidates : set[tuple[str, str]],
        Services that could be IHR for some DB (pairs (IHR, DB))
    ihr_violators : set[tuple[str, str]],
        Services that could be IHR for some DB, but they also call other services
        (pairs (IHR, DB))
    database_call_violators : set[str],
        Services from database_services that call other services
    databaser_no_ihr_violators : set[str],
        Services from database_services that have no apparent IHR
    """

    if database_services is None: database_services = set()

    D = nx.DiGraph(G)

    ihr_candidates = set()
    ihr_violators = set()
    database_call_violators = set()
    database_no_ihr_violators = database_services.copy()

    for node, out_degree in D.out_degree():
        zero_degree = out_degree == 0
        is_database = node in database_services
        if zero_degree or is_database:
            if len(preds := D.pred[node]) == 1:
                pred = [n for n in preds.keys()][0]
                if len(D.succ[pred]) == 1:
                    ihr_candidates.add((pred, node))
                    print(f"{user}: Information Holder Resource - '{pred}' is a"
                          f" potential IHR for '{node}'")
                else:
                    ihr_violators.add((pred, node))
                    print(f"{user}: Information Holder Resouce Violation - "
                          f"'{node}' is only accessed through '{pred}', but "
                          f"'{pred}' calls other services as well.")
                database_no_ihr_violators.discard(node)
        if not zero_degree and is_database:
            database_call_violators.add(node)
            print(f"{user}: Information Holder Resource Violation - '{node}'"
                  f" is designated as database service but has outgoing calls"
                  f"({out_degree=})")

    for service in database_no_ihr_violators:
        print(f"{user}: Information Holder Resource Violation - '{service}' "
              f"is designated as database service but no IHR detected.")

    return ihr_candidates, ihr_violators, database_call_violators, database_no_ihr_violators
