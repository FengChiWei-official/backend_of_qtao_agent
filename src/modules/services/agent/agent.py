from typing import Any
import sys
import json
import copy
import logging
from datetime import datetime
import threading

from src.utils.root_path import get_root_path
if str(get_root_path()) not in sys.path:
    sys.path.append(str(get_root_path()))

from .state import State
from .parser import LLMOutputParser
from .prompt_builder import PromptBuilder

from src.modules.services.business.record_bussiness import DialogueRecordBusiness
from src.utils.chatgpt import feed_LLM_full, gather_llm_output
from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.service_basis.user_info import UserInfo
from src.modules.services.service_basis.basis.tool import Tool

logger = logging.getLogger(__name__)

class Agent():
    """
    Agent类用于处理对话状态和上下文管理。
    Refactored to separate concerns: Logic (Agent), Data (State), Parsing (Parser), View (PromptBuilder).
    """

    def __init__(self, user_id: str, conversation_id: str, record_business: DialogueRecordBusiness, tools: Registry, prompt_template: str):
        # State 只负责数据存储
        self.state = State(user_id, conversation_id, record_business)
        
        # PromptBuilder 负责构建 Prompt
        self.prompt_builder = PromptBuilder(prompt_template, str(tools), tools.list_services())
        
        self.llm = gather_llm_output(feed_LLM_full)
        self.tools = tools
        self.user_info = UserInfo(user_id=user_id, ticket_info={})
        self.lock = threading.Lock()

    def __call__(self, query: str) -> dict:
        self.state.init_query(query)
        
        while True:
            # 1. Build Prompt (View)
            messages = self.prompt_builder.build(
                query=query,
                history=self.state.get_history(),
                context=self.state.get_context()
            )
            
            logger.debug(f"Prompt Messages: {messages}")
            
            # 2. LLM Call (IO)
            response = self.llm(messages)
            logger.debug(f"LLM response: {response}")

            # 3. Logic & Control Flow
            
            # Check for Final Answer first
            if LLMOutputParser.is_final_answer(response):
                try:
                    final_res = LLMOutputParser.parse_final_answer(response)
                    self.state.set_final_answer(final_res)
                    self.state.save_to_db()
                    break 
                except ValueError as e:
                     logger.error(f"Error parsing Final Answer: {e}")
                     # Continue to treat as thought/action or retry?
                     # If parsing failed but "Final Answer" is present, it's risky to continue.
                     # But for now, let's treat it as a normal response that might be malformed.
                     pass 

            # Parse Thought/Action
            parsed_ta = LLMOutputParser.parse_thought_action(response)
            self.state.set_thought_action(parsed_ta)
            
            action_name = parsed_ta.get("action")
            action_input = parsed_ta.get("action_input")

            # Check loop limit
            if self.state.looper.is_maxed_out():
                logger.warning("Maximum loop count reached; generating final answer.")
                fallback_dict = {
                    "thought": "Max steps reached",
                    "answer": "I'm sorry, I couldn't arrive at a final answer within the allowed number of steps.",
                    "picture": []
                }
                self.state.set_final_answer(fallback_dict)
                self.state.save_to_db()
                break
            
            self.state.looper.increment()

            # Execute Tool
            tools_output = ""
            if action_name == "ERROR":
                 tools_output = f"Format Error: Could not parse Thought and Action from your response. Please follow the format strictly.\nExpected format:\nThought: ...\nAction: ...\nAction Input: ..."
            elif not action_name:
                 logger.warning("LLM did not provide an action name; skipping tool call. action_input=%s", action_input)
                 tools_output = f"No action produced by LLM. action_input={action_input}"
            else:
                 try:
                     service: Tool = self.tools.get_service(action_name)
                     copy_input = copy.deepcopy(action_input)
                     
                     # Build history for tool (without system prompt)
                     tool_history = self.prompt_builder.build(
                        query=query,
                        history=self.state.get_history(),
                        context=self.state.get_context(),
                        include_system_prompt=False
                     )
                     
                     tools_output = service(
                        copy_input, 
                        self.user_info,
                        tool_history
                     )
                     
                     # Serialize tool output to JSON
                     try:
                        tools_output = json.dumps(tools_output, ensure_ascii=False, default=str)
                     except Exception:
                        tools_output = str(tools_output)
                        
                 except KeyError:
                    logger.error(f"Service '{action_name}' not found in tools registry.")
                    tools_output = f"Service '{action_name}' not found. Please check the service name and try again."
                 except Exception as e:
                    logger.error(f"Error executing tool '{action_name}': {e}")
                    tools_output = f"Error executing tool '{action_name}': {str(e)}"

            # Update Observation (Data)
            self.state.update_observation(tools_output)

        return self.state.get_final_result()

    def stream_call(self, query: str) -> Any:
        """
        Stream-based call to process query with streaming responses.
        Yields intermediate results as they become available.
        """
        self.state.init_query(query)
        
        while True:
            # 1. Build Prompt (View)
            messages = self.prompt_builder.build(
                query=query,
                history=self.state.get_history(),
                context=self.state.get_context()
            )
            
            logger.debug(f"Prompt Messages: {messages}")
            
            # 2. LLM Call with streaming (IO)
            response = ""
            try:
                for chunk in feed_LLM_full(messages):
                    if chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        response += delta
                        # Yield streaming tokens as they arrive
                        yield {"type": "token", "content": delta}
            except Exception as e:
                logger.error(f"Error during LLM streaming: {e}")
                yield {"type": "error", "content": str(e)}
                break
            
            logger.debug(f"LLM response: {response}")

            # 3. Logic & Control Flow
            
            # Check for Final Answer first
            if LLMOutputParser.is_final_answer(response):
                try:
                    final_res = LLMOutputParser.parse_final_answer(response)
                    self.state.set_final_answer(final_res)
                    self.state.save_to_db()
                    yield {"type": "final_answer", "content": final_res}
                    break 
                except ValueError as e:
                     logger.error(f"Error parsing Final Answer: {e}")
                     pass 

            # Parse Thought/Action
            parsed_ta = LLMOutputParser.parse_thought_action(response)
            self.state.set_thought_action(parsed_ta)
            
            action_name = parsed_ta.get("action")
            action_input = parsed_ta.get("action_input")

            # Check loop limit
            if self.state.looper.is_maxed_out():
                logger.warning("Maximum loop count reached; generating final answer.")
                fallback_dict = {
                    "thought": "Max steps reached",
                    "answer": "I'm sorry, I couldn't arrive at a final answer within the allowed number of steps.",
                    "picture": []
                }
                self.state.set_final_answer(fallback_dict)
                self.state.save_to_db()
                yield {"type": "final_answer", "content": fallback_dict}
                break
            
            self.state.looper.increment()

            # Execute Tool
            tools_output = ""
            if action_name == "ERROR":
                 tools_output = f"Format Error: Could not parse Thought and Action from your response. Please follow the format strictly.\nExpected format:\nThought: ...\nAction: ...\nAction Input: ..."
            elif not action_name:
                 logger.warning("LLM did not provide an action name; skipping tool call. action_input=%s", action_input)
                 tools_output = f"No action produced by LLM. action_input={action_input}"
            else:
                 try:
                     service: Tool = self.tools.get_service(action_name)
                     copy_input = copy.deepcopy(action_input)
                     
                     # Build history for tool (without system prompt)
                     tool_history = self.prompt_builder.build(
                        query=query,
                        history=self.state.get_history(),
                        context=self.state.get_context(),
                        include_system_prompt=False
                     )
                     
                     # Yield tool execution info
                     yield {"type": "tool_start", "tool": action_name, "input": copy_input}
                     
                     tools_output = service(
                        copy_input, 
                        self.user_info,
                        tool_history
                     )
                     
                     # Serialize tool output to JSON
                     try:
                        tools_output = json.dumps(tools_output, ensure_ascii=False, default=str)
                     except Exception:
                        tools_output = str(tools_output)
                     
                     # Yield tool result
                     yield {"type": "tool_result", "tool": action_name, "result": tools_output}
                        
                 except KeyError:
                    logger.error(f"Service '{action_name}' not found in tools registry.")
                    tools_output = f"Service '{action_name}' not found. Please check the service name and try again."
                    yield {"type": "tool_error", "tool": action_name, "error": tools_output}
                 except Exception as e:
                    logger.error(f"Error executing tool '{action_name}': {e}")
                    tools_output = f"Error executing tool '{action_name}': {str(e)}"
                    yield {"type": "tool_error", "tool": action_name, "error": tools_output}

            # Update Observation (Data)
            self.state.update_observation(tools_output)