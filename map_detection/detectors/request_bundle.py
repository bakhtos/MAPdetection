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
