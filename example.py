import os
from datetime import timedelta

import map_detection

if __name__ == '__main__':
    
    directory = "kubernetes-istio-sleuth-v0.2.1-separate-load"
    pptam_dir = os.path.join(directory, 'pptam')
    tracing_dir = os.path.join(directory, 'tracing-log')
    time_delta = timedelta(hours=-8)
    user_graphs, pipelines = map_detection.generate_call_graphs(pptam_dir, tracing_dir, time_delta)
    '''detections = dict()
    for user, G in user_graphs.items():
        detections[("request_bundle", user)] = map_detection.detectors.detect_request_bundle(pipelines[user], user=user)
        detections[("frontend_integration", user)] = map_detection.detectors.detect_frontend_integration(G, frontend_services={'ts-ui-dashboard'}, user=user)
        detections[("information_holder_resource", user)] = map_detection.detectors.detect_information_holder_resource(G, user=user)
    '''
    map_detection.utils.write_pipelines(pipelines)
    #draw_graph(G, intervals)
