from typing import Any
from .state import State
from src.utils.root_path import get_root_path
import sys
import json
if str(get_root_path()) not in sys.path:
    sys.path.append(str(get_root_path()))
import threading

from src.modules.services.business.record_bussiness import DialogueRecordBusiness  # 修正import路径
from src.utils.chatgpt import feed_LLM_full, gather_llm_output
from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.service_basis.user_info import UserInfo
import copy

import logging
logger = logging.getLogger(__name__)

from datetime import datetime

class Agent():
    """
    Agent类用于处理对话状态和上下文管理。
    """

    def __init__(self, user_id: str, conversation_id: str, record_business: DialogueRecordBusiness, tools: Registry, prompt_template: str):
        self.state = State(user_id, conversation_id, record_business, prompt_template, str(tools), tools.list_services())
        self.llm = gather_llm_output(feed_LLM_full)
        self.tools = tools
        self.user_info = UserInfo(user_id=user_id, ticket_info={})
        self.lock = threading.Lock()

    def __call__(self, query: str) -> dict:
        query_sent_at = datetime.now()
        self.state.handle_user_query(query)
        
        
        while True:
            check_prompt = self.state.generate_history_with_context_and_prompt()
            logger.debug(str(check_prompt))
            response = self.llm(self.state.generate_history_with_context_and_prompt())
            logger.debug(f"LLM response: {response}")  # 记录 response 内容

            self.state.handle_llm_response_and_try_to_stop(response)
            
            if self.state.looper.is_maxed_out():
                break
            self.state.looper.increment()

            action_name, action_input = self.state.generate_action_input_for_tools()
            # If the LLM did not produce an action name, skip calling tools and record observation
            if not action_name:
                logger.warning("LLM did not provide an action name; skipping tool call. action_input=%s", action_input)
                tools_output = f"No action produced by LLM. action_input={action_input}"
                # feed the observation back into the state so the agent can continue
                self.state.handle_observation(tools_output)
                # continue loop to let LLM respond again (or break by looper)
                continue

            try:
                service = self.tools.get_service(action_name)
                # Pass a deep copy of action_input to tools so they don't mutate the State's internal dict
                #tools_output = str(service(copy.deepcopy(action_input), self.user_info, self.state.generate_history_with_context_and_prompt(is_containing_prompt=False)))
                copy_input = json.loads(json.dumps(action_input))  # another way to deep copy
                tools_output = str(copy_input, self.user_info, self.state.generate_history_with_context_and_prompt(is_containing_prompt=False))
            
            except KeyError:
                logger.error(f"Service '{action_name}' not found in tools registry.")
                tools_output = f"Service '{action_name}' not found. Please check the service name and try again."

            check_prompt = self.state.generate_history_with_context_and_prompt()
            logger.debug(f"check_prompt: {check_prompt}")
            self.state.handle_observation(tools_output)

        return self.state.generate_final_answer()