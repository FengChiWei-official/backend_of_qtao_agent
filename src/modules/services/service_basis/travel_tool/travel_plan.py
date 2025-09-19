import sys
import time

from src.modules.services.service_basis.basis.tool import Tool
from src.modules.services.service_basis.travel_tool.chinatravel.agent.llms import (
    Deepseek,
    GLM4Plus,
    GPT4o,
)
from src.modules.services.service_basis.travel_tool.chinatravel.agent.nesy_agent.llm_driven_rec import (
    LLMDrivenAgent as NesyAgent,
)
from src.modules.services.service_basis.travel_tool.chinatravel.environment.world_env import (
    WorldEnv,
)
from src.modules.services.service_basis.user_info import UserInfo

env = WorldEnv()

travelplan_desc = '''旅行规划：本接口为用户定制个性化的旅游方案，其囊括旅行途中每一天的交通、景点、餐馆和酒店。本接口输入格式为：{"用户需求": <用户需求>, "出发城市": <出发城市>, "目标城市": <目标城市>, "游玩天数": <游玩天数>, "人数": <人数>}，其中<用户需求>是结合对话历史对用户当前旅行规划需求的全面且准确的总结。注意推断出发城市和目标城市，**确保出发和目标城市不相同，否则tool会失效！**'''

class TravelPlan(Tool):
    def __init__(self, name="旅行规划", description=travelplan_desc, llm="deepseek"):
        super().__init__(name, description)

        env = WorldEnv()    # Question: 这个WorldEnv()是用来干嘛的？

        if llm == "deepseek":
            llm = Deepseek()
        elif llm == "gpt-4o":
            llm = GPT4o()
        elif llm == "glm4-plus":
            llm = GLM4Plus()

        cache_dir = "cache"

        self.agent = NesyAgent(env=env, backbone_llm=llm, cache_dir=cache_dir, search_width=30, debug=True, method="NeSy")

    def __call__(self, parameter: dict, user_info: UserInfo, history: list) -> dict:
        beg_time = time.time()
        query = {
            "uid": f"test_{len(history)-1}t", 
            "nature_language": parameter.get('用户需求'),
            "start_city": parameter.get('出发城市'),
            "target_city": parameter.get('目标城市'),
            "days": parameter.get('游玩天数'),
            "people_number": parameter.get('人数')
        }
        succ, plan = self.agent.run(query, load_cache=False, oralce_translation=False)
        end_time = time.time()
        print(f"本次规划耗时：{end_time-beg_time:.3f}s")

        return plan
