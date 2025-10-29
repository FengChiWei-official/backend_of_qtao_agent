import os, sys
from typing import Dict, Type

from .utils import PATH_TO_ROOT
if str(PATH_TO_ROOT) not in sys.path:
    sys.path.append(str(PATH_TO_ROOT))

from src.modules.services.service_basis.basis.tool import Tool


class Registry:
    def __init__(self):
        self._services: Dict[str, Tool] = {}

    def register(self, service_instance):
        """
        Registers a service instance in the registry.
        # **WARNING: YOU CAN NOT REGISTER ANY STATE-FUL SERVICES, ALL SERVICES MUST BE STATELESS!**
        :param service_instance: An instance of Tool or its subclass.
        :raises KeyError: If the service name is already registered.
        :raises TypeError: If the service_instance is not an instance of Tool or its subclass.
        """
        
        # tool type guards that the service_instance is a subclass of Tool
        if not isinstance(service_instance, Tool):
            raise TypeError("service_instance must be an instance of Tool or its subclass.")
        
        # tool type guards that the service_instance has a name attribute
        if service_instance.name in self._services:
            raise KeyError(f"Service '{service_instance.name}' is already registered.")
        
        self._services[service_instance.name] = service_instance

    def get_service(self, service_name:str) -> Tool:
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' is not registered.")
        return self._services[service_name]

    def list_services(self) -> list[str]:
        return list(self._services.keys())

    def __repr__(self) -> str:
        description = "[" + ", \n".join(str(service) for service in self._services.values()) + "]"
        return f"Tools are: ({description})"


class FactoryRegistry:
    """
    注册Tool类，每次get_service返回新实例，适合有状态/重计算服务。
    """
    def __init__(self):
        self._service_classes: Dict[str, Dict[str, Type[Tool] | str]] = {}
        """
        Maps service names to their class types and descriptions.
        service_name -> {
            "class": Tool subclass,
            "name": str,
            "description": str
        }
        """

    def register(self, service_class: Type[Tool], name: str, description: str) -> None:
        """
        Registers a service class in the factory registry.
        :param service_class: The service class to register.
        :param name: The name of the service.
        :param description: A brief description of the service.
        :raises KeyError: If the service name is already registered.
        :raises TypeError: If the service_class is not a subclass of Tool.
        """
        if not issubclass(service_class, Tool):
            raise TypeError("service_class must be a subclass of Tool.")
        if name in self._service_classes:
            raise KeyError(f"Service '{name}' is already registered.")
        self._service_classes[name] = {
            "class": service_class,
            "name": name,
            "description": description
        }

    def get_service(self, service_name: str, *args, **kwargs) -> Tool:
        if service_name not in self._service_classes:
            raise KeyError(f"Service '{service_name}' is not registered.")
        service_dict = self._service_classes[service_name]
        service_class = service_dict["class"]
        if isinstance(service_class, str):
            raise TypeError(f"Registered class for '{service_name}' is not a subclass of Tool.")
        if not issubclass(service_class, Tool):
            raise TypeError(f"Registered class for '{service_name}' is not a subclass of Tool.")
        # 如果调用时传了参数，则用调用者的参数，否则用注册时的 name/description
        if args or kwargs:
            return service_class(*args, **kwargs)
        else:
            return service_class(service_dict["name"], service_dict["description"])

    def list_services(self) -> list[str]:
        return list(self._service_classes.keys())

    def __repr__(self) -> str:
        description = "[" + \
        ", \n".join(
            f"""{name}: {info['description']}"""
            for name, info in self._service_classes.items()
        ) \
        + "]"
        return f"Tool classes: {description}"


