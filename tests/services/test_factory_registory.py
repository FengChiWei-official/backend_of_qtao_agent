import pytest
from datetime import datetime
import random
from src.modules.services.service_basis.ToolRegistry import FactoryRegistry, Tool
from src.modules.services.service_basis.user_info import UserInfo


class DummyTool(Tool):
    def __init__(self, name="dummy", description="desc"):
        super().__init__(name, description)
    def __call__(self, *args, **kwargs):
        return "ok"

concurrent_dependency = [1, 2, 3]
class ConcurrentDummyTool(Tool):
    def __init__(self, name="concurrent_dummy", description="concurrent desc", num=1):
        super().__init__(name, description)
        self.num = num
    def __call__(self, *args, **kwargs):
        start = datetime.now()
        finish_duration = 20 + random.randint(0, 10)
        while (datetime.now() - start).seconds < finish_duration:
            for item in concurrent_dependency:
                print(f"Processing {item}")
        return f"concurrent{self.num} ok"

dummy_arg = {
    "parameter" : {},
    "user_info" : UserInfo("362531200504090911"),
    "history" : [],
}
def test_register_and_get_service():
    registry = FactoryRegistry()
    registry.register(DummyTool, "dummy", "desc")
    assert "dummy" in registry.list_services()
    tool = registry.get_service("dummy")
    assert isinstance(tool, DummyTool)
    assert tool.name == "dummy"
    assert tool.description == "desc"
    assert tool(**dummy_arg) == "ok"

def test_duplicate_register():
    registry = FactoryRegistry()
    registry.register(DummyTool, "dummy", "desc")
    with pytest.raises(KeyError):
        registry.register(DummyTool, "dummy", "desc2")

def test_get_unregistered():
    registry = FactoryRegistry()
    with pytest.raises(KeyError):
        registry.get_service("notfound")

def test_type_check():
    registry = FactoryRegistry()
    class NotATool:
        pass
    with pytest.raises(TypeError):
        registry.register(NotATool, "notatool", "desc")  # type: ignore

def test_repr():
    registry = FactoryRegistry()
    registry.register(DummyTool, "dummy", "desc")
    repr_str = repr(registry)
    assert "Tool classes: [" in repr_str
    assert "dummy: desc" in repr_str

def test_repr_empty():
    registry = FactoryRegistry()
    repr_str = repr(registry)
    assert "Tool classes: []" in repr_str
    assert "[]" in repr_str
#测并发
def test_concurrent_get():
    registry = FactoryRegistry()
    registry.register(ConcurrentDummyTool, "concurrent_dummy", "concurrent desc")
    assert "concurrent_dummy" in registry.list_services()
    tool1 = registry.get_service("concurrent_dummy", "concurrent_dummy",  "desc","1")
    tool2 = registry.get_service("concurrent_dummy", "concurrent_dummy", ""desc, "2")
    assert isinstance(tool1, ConcurrentDummyTool)
    assert isinstance(tool2, ConcurrentDummyTool)
    assert tool1.name == "concurrent_dummy"
    assert tool2.name == "concurrent_dummy"
    assert tool1.description == "concurrent desc"
    assert tool2.description == "concurrent desc"
    
    # 创建并发环境
    # 这里可以使用多线程或异步来测试并发调用
    # 例如使用 threading 或 asyncio 来创建多个线程/任务调用 tool1 和 tool2
    import threading
    threads = []
    t1 = threading.Thread(target=tool1)
    t2 = threading.Thread(target=tool2)
    threads.append(t1)
    threads.append(t2)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # 确认并发调用没有问题
    assert tool1() == "concurrent1 ok"
    assert tool2() == "concurrent2 ok"

from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.service_basis.meal_service import MealService
import time

def test_concurrent_execution():
    f_registry = FactoryRegistry()
    f_registry.register(MealService, "meal_service", "A service for meal-related tasks")

    registry = Registry()
    registry.register(MealService())
    assert "meal_service" in registry.list_services()

    def execute_service(ins, *args, **kwargs):
        start = time.time()
        result = ins(*args, **kwargs)
        assert result is not None
        end = time.time()
        duration = end - start
        return result, duration

    import concurrent.futures
    n = 5
    # FactoryRegistry 并发
    start_factory = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
        futures = [executor.submit(execute_service, f_registry.get_service("meal_service")) for _ in range(n)]
        factory_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    end_factory = time.time()
    factory_total = end_factory - start_factory
    print(f"FactoryRegistry total time: {factory_total:.2f}s")
    for result, duration in factory_results:
        print(f"Factory result: {result}, Duration: {duration:.2f}s")

    # Registry 并发
    start_singleton = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
        singleton_instance = registry.get_service("meal_service")
        futures = [executor.submit(execute_service, singleton_instance) for _ in range(n)]
        singleton_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    end_singleton = time.time()
    singleton_total = end_singleton - start_singleton
    print(f"Registry total time: {singleton_total:.2f}s")
    for result, duration in singleton_results:
        print(f"Registry result: {result}, Duration: {duration:.2f}s")

    # 可选：断言两者的总耗时或平均耗时差异
    assert factory_total <= singleton_total

if __name__ == "__main__":
    pytest.main([__file__])