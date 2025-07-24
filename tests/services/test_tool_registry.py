import unittest
from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.service_basis.basis.tool import Tool

class DummyTool(Tool):
    def __init__(self, name):
        super().__init__(name, description="dummy")
    def __call__(self, *args, **kwargs):
        return "dummy"

class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = Registry()
        self.tool1 = DummyTool("服务A")
        self.tool2 = DummyTool("服务B")

    def test_register_and_get(self):
        self.registry.register(self.tool1)
        self.assertIs(self.registry.get_service("服务A"), self.tool1)

    def test_list_services(self):
        self.registry.register(self.tool1)
        self.registry.register(self.tool2)
        self.assertListEqual(sorted(self.registry.list_services()), ["服务A", "服务B"])

    def test_duplicate_register(self):
        self.registry.register(self.tool1)
        with self.assertRaises(ValueError):
            self.registry.register(DummyTool("服务A"))

    def test_type_guard(self):
        with self.assertRaises(TypeError):
            self.registry.register(object())

    def test_get_service_not_found(self):
        with self.assertRaises(ValueError):
            self.registry.get_service("不存在")

    def test_list_empty_registry(self):
        self.assertListEqual(self.registry.list_services(), [])

    def call_registered_service(self, service):
        if service in self.registry.list_services():
            return self.registry.get_service(service)()
        else:
            raise ValueError(f"Service {service} not found in registry.")

if __name__ == "__main__":
    unittest.main()
