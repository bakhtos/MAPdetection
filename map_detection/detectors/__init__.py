from .frontend_integration import detect_frontend_integration
from .request_bundle import detect_request_bundle
from .information_holder_resource import detect_information_holder_resource

__all__ = ['detect_request_bundle',
           'detect_frontend_integration',
           'detect_information_holder_resource']
