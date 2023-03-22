__all__ = ['detect_patterns']

import map_detection.detectors.frontend_integration
import map_detection.detectors.information_holder_resource


def detect_patterns(G):
    map_detection.detectors.frontend_integration.detect_frontend_integration(G)
    map_detection.detectors.information_holder_resource.detect_information_holder_resource(G)