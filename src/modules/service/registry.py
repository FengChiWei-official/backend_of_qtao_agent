from src.modules.service.utils import Tool


class Registory:
    def __init__(self):
        self._services = {}

    def register(self, service_instance):
        if service_name in self._services:
            raise ValueError(f"Service '{service_name}' is already registered.")
        # tool type guards that the service_instance is a subclass of Tool
        if not isinstance(service_instance, Tool):
            raise TypeError("service_instance must be an instance of Tool or its subclass.")
        else:
            service_instance:Tool = service_instance
        self._services[service_instance.name] = service_instance

    def get_service(self, service_name):
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' is not registered.")
        return self._services[service_name]

    def list_services(self):
        return list(self._services.keys())

    def __repr__(self):
