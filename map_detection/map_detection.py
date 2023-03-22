__all__ = ['detect_patterns']

from map_detection import detectors


def detect_patterns(G):
    detectors.detect_frontend_integration(G)
    detectors.detect_information_holder_resource(G)