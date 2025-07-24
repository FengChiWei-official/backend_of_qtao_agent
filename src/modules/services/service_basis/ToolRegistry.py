import os, sys

from .utils import PATH_TO_ROOT
if str(PATH_TO_ROOT) not in sys.path:
    sys.path.append(str(PATH_TO_ROOT))

from src.modules.services.service_basis.basis.tool import Tool


class Registry:
    def __init__(self):
        self._services = {}

    def register(self, service_instance):
        """
        Registers a service instance in the registry.
        :param service_instance: An instance of Tool or its subclass.
        :raises ValueError: If the service name is already registered.
        :raises TypeError: If the service_instance is not an instance of Tool or its subclass.
        """
        
        # tool type guards that the service_instance is a subclass of Tool
        if not isinstance(service_instance, Tool):
            raise TypeError("service_instance must be an instance of Tool or its subclass.")
        
        # tool type guards that the service_instance has a name attribute
        if service_instance.name in self._services:
            raise ValueError(f"Service '{service_instance.name}' is already registered.")
        
        self._services[service_instance.name] = service_instance

    def get_service(self, service_name):
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' is not registered.")
        return self._services[service_name]

    def list_services(self) -> list[str]:
        return list(self._services.keys())

    def __repr__(self) -> str:
        description = "[" + ", \n".join(str(service) for service in self._services.values()) + "]"
        return f"Tools are: ({description})"
