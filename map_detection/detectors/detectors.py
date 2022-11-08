import networkx as nx

__all__ = ['detect_request_bundle', 'detect_frontend_integration',
           'detect_information_holder_resource']


def detect_request_bundle(pipeline, threshold_service=2,
                          threshold_endpoint=2, user='NoUser'):
    """Detect request bundle anti-pattern, i.e. consecutive calls between same services.

    Bundles are detected on service level (service A repeatedly calls same service B)
    and endpoint level (service A repeatedly calls same endpoint of same service B).
    Results are returned as dicts from users to a list of detected bundles, each
    bundle is a tuple of the form (from_service, to_service, count) for service-level detection
    and (from_service, to_service, endpoint, count) for endpoint-level detection.

    pipelines : list[tuple[datetime, str, str, str]],
        A list containing a call pipeline for a user (one of the items in
        pipelines returned by parse_logs())
    threshold_service : int, optional (default 2)
        Minimum count of consecutive calls necessary to make up a bundle in
        service-level detection (default = 2, i.e. any repeated call
                                 makes a bundle)
    threshold_endpoint : int, optional (default 2)
        Minimum count of consecutive calls necessary to make up a bundle in
        endpoint-level detection (default = 2, i.e. any repeated call
                                  makes a bundle)
    user : str, optional (default 'NoUser')
        User's name to put in logs

    Returns
    _______
    bundles_service : list[tuple[str, str, int]],
        Detected bundles in service-level detection
    bundles_endpoint : list[tuple[str, str, str, int]],
        Detected bundles in endpoint-level detection
    """

    bundles_service = []
    bundles_endpoint = []
    last_call_service = None
    last_call_endpoint = None
    count_service = 1
    count_endpoint = 1
    for (time, from_service, to_service, endpoint) in pipeline:
        current_call_service = from_service, to_service
        current_call_endpoint = from_service, to_service, endpoint
        if current_call_service == last_call_service:
            count_service += 1
        else:
            if count_service >= threshold_service:
                bundles_service.append((*last_call_service, count_service))
                print(f"{user}: Service-level request bundle detected between "
                      f"{last_call_service[0]} and {last_call_service[1]} "
                      f"with count {count_service}")
            count_service = 1
            last_call_service = current_call_service
                
        if current_call_endpoint == last_call_endpoint:
            count_endpoint += 1
        else:
            if count_endpoint >= threshold_endpoint:
                bundles_endpoint.append((*last_call_endpoint, count_endpoint))
                print(f"{user}: Endpoint-level request bundle detected between "
                      f"{last_call_endpoint[0]} and {last_call_endpoint[1]}"
                      f"{last_call_endpoint[2]} with count {count_endpoint}")
            count_endpoint = 1
            last_call_endpoint = current_call_endpoint

    return bundles_service, bundles_endpoint

def detect_frontend_integration(G, frontend_services=None, user=None):

    if frontend_services is None: frontend_services = set()
    if user is None: user = "NoUser"

    D = nx.DiGraph(G)

    frontend_candidates = set()
    frontend_violators = set()

    for node, in_degree in D.in_degree():
        if in_degree == 0:
            if D.out_degree(node) > 0:
                frontend_candidates.add(node)
                print(f"{user}: Frontend Integreation - potential frontend service '{node}' found.")
        elif node in frontend_services:
            frontend_violators.add(node)
            print(f"{user}: Frontend Integration Violation - service '{node}' "
                  f"is designated as frontend service but has incoming calls "
                  f"(in-degree = {in_degree})")

    return frontend_candidates, frontend_violators


def detect_information_holder_resource(G, database_services=None, user=None):

    if database_services is None: database_services = set()
    if user is None: user = "NoUser"

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
                pred = [n for n in preds.keys()]
                pred = pred[0]
                if len(D.succ[pred]) == 1:
                    ihr_candidates.add((pred, node))
                    print(f"{user}: Information Holder Resource - '{pred}' is a "
                          f"potential IHR for '{node}'")
                else:
                    ihr_violators.add((pred, node))
                    print(f"{user}: Information Holder Resouce Violation - "
                          f"'{node}' is only accessed through '{pred}', but "
                          f"'{pred}' calls other services as well.")
                database_no_ihr_violators.discard(node)
        if not zero_degree and is_database:
            database_call_violators.add(node)
            print(f"{user}: Information Holder Resource Violation - '{node}' is designated"
                  f" as database service but has outgoing calls (out-dergee = {out_degree})")

    for service in database_services:
        print(f"{user}: Information Holder Resource Violation - '{service}' "
              f"is designated as database service but no IHR detected.")
    
    return ihr_candidates, ihr_violators, database_call_violators, database_no_ihr_violators
