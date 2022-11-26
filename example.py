import os
from datetime import timedelta

from map_detection import generate_call_graphs
from map_detection.detectors import *
from map_detection.utils import write_pipelines

ROOT_DIR = "kubernetes-istio-sleuth-v0.2.1-separate-load"
PPTAM_DIR = os.path.join(ROOT_DIR, 'pptam')
TRACING_DIR = os.path.join(ROOT_DIR, 'tracing-log')
TIME_DELTA = timedelta(hours=-8)
FRONTEND_SERVICES = {'ts-ui-dashboard'}
DATABASE_SERVICES = {'ts-assurance-mongo',
                     'ts-auth-mongo',
                     'ts-config-mongo',
                     'ts-consign-mongo',
                     'ts-consign-price-mongo',
                     'ts-contacts-mongo',
                     'ts-delivery-mongo',
                     'ts-food-map-mongo',
                     'ts-food-mongo',
                     'ts-inside-payment-mongo',
                     'ts-notification-mongo',
                     'ts-order-mongo',
                     'ts-order-other-mongo',
                     'ts-payment-mongo',
                     'ts-price-mongo',
                     'ts-route-mongo',
                     'ts-security-mongo',
                     'ts-station-mongo',
                     'ts-ticket-office-mongo',
                     'ts-train-mongo',
                     'ts-travel2-mongo',
                     'ts-travel-mongo',
                     'ts-user-mongo',
                     'ts-voucher-mysql'}

if __name__ == '__main__':
    user_graphs, pipelines = generate_call_graphs(PPTAM_DIR,
                                                  TRACING_DIR,
                                                  TIME_DELTA)
    detections = dict()
    for user, G in user_graphs.items():
        detections[("request_bundle", user)] = detect_request_bundle(
                                                pipelines[user], user=user)
        detections[("frontend_integration", user)] =\
            detect_frontend_integration(G, frontend_services={'ts-ui-dashboard'},
                                        user=user)
        detections[("information_holder_resource", user)] =\
            detect_information_holder_resource(G, database_services=DATABASE_SERVICES,
                                               user=user)
    write_pipelines(pipelines)
