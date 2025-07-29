import time
import concurrent.futures
from src.modules.services.service_basis.meal_service import MealService
from src.modules.services.service_basis.user_info import UserInfo
# 假设FactoryRegistry和Registry已在工程中实现并可导入
from src.modules.services.service_basis.ToolRegistry import FactoryRegistry, Tool, Registry
from typing import Type, Dict

test_param = {
    "parameter": {},
    "user_info": UserInfo("362531200504090911"),
    "history": [{"role": "user", "content": "推荐一个粤菜?"}],
}
test_param_f = {
    "parameter": {},
    "user_info": UserInfo("362531200504090911"),
    "history": [{"role": "user", "content": "推荐一个川菜?"}],
}

def test_concurrent_execution():
    f_registry = FactoryRegistry()
    f_registry.register(MealService, "meal_service", "A service for meal-related tasks")

    registry = Registry()
    registry.register(MealService("meal_service", "A service for meal-related tasks"))
    assert "meal_service" in registry.list_services()

    def execute_service(ins, *args, **kwargs):
        start = time.time()
        result = ins(*args, **kwargs)
        assert result is not None
        end = time.time()
        duration = end - start
        return result, duration

    n = 2
    # FactoryRegistry 并发
    start_factory = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
        futures = [executor.submit(execute_service, f_registry.get_service("meal_service"), **test_param_f) for _ in range(n)]
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
        futures = [executor.submit(execute_service, singleton_instance, **test_param) for _ in range(n)]
        singleton_results = [future.result() for future in concurrent.futures.as_completed(futures)]
    end_singleton = time.time()
    singleton_total = end_singleton - start_singleton
    print(f"Registry total time: {singleton_total:.2f}s")
    for result, duration in singleton_results:
        print(f"Registry result: {result}, Duration: {duration:.2f}s")

    # 可选：断言两者的总耗时或平均耗时差异
    assert factory_total <= singleton_total

    with open("./results.txt", "a") as f:
        f.write(f"FactoryRegistry total time: {factory_total:.2f}s\n")
        f.write(f"Registry total time: {singleton_total:.2f}s\n")
        f.write(f"Factory results: {factory_results}\n")
        f.write(f"Registry results: {singleton_results}\n")
        f.write(f"Registry end: {end_singleton:.2f}s\n")
        f.write(f"Factory end: {end_factory:.2f}s\n")

if __name__ == "__main__":
    test_concurrent_execution()
