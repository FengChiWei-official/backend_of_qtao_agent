import sys
import time
import os

if __name__ == "__main__":
    import sys, os
    from pathlib import Path
    def get_root_path() -> Path:
        for i in range(10):
            t = Path(__file__).resolve().parents[i]
            if "backend" in t.name or "app" in t.name:
                return t
        raise FileNotFoundError("Project root not found in the expected directory structure.")
    PATH_TO_ROOT = get_root_path()
    sys.path.append(str(PATH_TO_ROOT))
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))

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

# travelplan_desc = '''旅行规划：本接口为用户定制个性化的旅游方案，其囊括旅行途中每一天的交通、景点、餐馆和酒店。本接口输入格式为：{"用户需求": <用户需求>}，其中<用户需求>是结合对话历史对用户当前旅行规划需求的全面且准确的总结。'''
travelplan_desc = '''
旅行规划：本接口为用户定制个性化的旅游方案，其囊括旅行途中每一天的交通、景点、餐馆和酒店。
本接口输入格式为：{"用户需求": <用户需求>, "出发城市": <出发城市>, "目标城市": <目标城市>, "游玩天数": <游玩天数>, "人数": <人数>}，
其中<用户需求>是结合对话历史对用户当前旅行规划需求的全面且准确的总结。

本工具的输出繁杂，请务必严格按照以下要求生成回答：
对于旅行规划，请按照时间顺序梳理观察到的工具输入，将每天涉及的城际交通（车次/航班代号，出发到达时间，距离，价钱等等），城内交通(类型，出发到达时间，距离，价钱等等)，景点（名字，票价等等），就餐点（名字，价钱，种类等等），酒店（名字，价钱等等）信息一一列出。当用户的主要目的是旅游规划时，请务必注意展示所有信息。
'''
# travelplan_desc = '''旅行规划：本接口为用户定制个性化的旅游方案，其囊括旅行途中每一天的交通、景点、餐馆和酒店。本接口输入格式为：{"用户需求": <用户需求>}，其中<用户需求>是结合对话历史对用户当前旅行规划需求的全面总结（请不要脑补用户没有提及的方面和细节）。'''
# travelplan_desc = '''旅行规划：本接口为用户定制个性化的旅游方案，其囊括旅行途中每一天的交通、景点、餐馆和酒店。本接口无需输入，因此Action_Input填None即可。'''

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


if __name__ == "__main__":
    tool = TravelPlan()
    parameter = {
        "用户需求": "我想去北京玩5天，预算2000元，喜欢历史文化和美食。",
        "出发城市": "上海",
        "目标城市": "北京",
        "游玩天数": 5,
        "人数": 1
    }
    user_info = UserInfo(user_id="450922196505072973")
    history = []
    res = tool(parameter, user_info, history)
    print(res)