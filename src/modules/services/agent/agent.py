from typing import Any
from .state import State
from src.utils.root_path import get_root_path
import sys
if str(get_root_path()) not in sys.path:
    sys.path.append(str(get_root_path()))
    
from src.modules.services.business.record_bussiness import DialogueRecordBusiness  # 修正import路径
from src.utils.chatgpt import feed_LLM_full, gather_llm_output
from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.service_basis.user_info import UserInfo
class Agent():
    """
    Agent类用于处理对话状态和上下文管理。
    """

    def __init__(self, user_id: str, conversation_id: str, record_bussiness: DialogueRecordBusiness, tools: Registry, prompt_template: str):
        self.state = State(user_id, conversation_id, record_bussiness, prompt_template, str(tools), tools.list_services())
        self.llm = gather_llm_output(feed_LLM_full)
        self.tools = tools
        self.user_info = UserInfo(user_id=user_id, ticket_info={})

    def __call__(self, query: str) -> dict:
        self.state.handle_user_query(query)
        
        while True:
            response = self.llm(self.state.generate_query_for_llm())
            self.state.handle_llm_response(response)
            
            if self.state.looper.is_maxed_out():
                break
            self.state.looper.increment()

            action_name, action_input = self.state.generate_action_input_for_tools()
            tools_output = self.tools.get_service(action_name)(action_input, self.user_info, self.state.generate_query_for_llm)
            self.state.handle_observation(tools_output)

        return self.state.generate_final_answer()