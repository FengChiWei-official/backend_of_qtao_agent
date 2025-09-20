import sys
import json
from src.utils.root_path import get_root_path
if str(get_root_path()) not in sys.path:
    sys.path.append(str(get_root_path()))

from .utils import Looper

from src.modules.services.service_basis.user_info import UserInfo  # Adjust the import path as needed
from ..business.record_bussiness import DialogueRecordBusiness # only for type hinting


import re
import datetime



# Define the State class to manage user state
class State:
    """
    Manages the state of a user.
    Attributes:
        user_id (str): Unique identifier for the user.
        user_info (UserInfo): User information instance.
    
    """

    """
    `dialogue history` is 3 layers:
    - `history`: List of finished conversation records, each mapping to a DialogueRecord row.
    - `context`: List of recent or relevant context records (e.g. last N rounds, or unfinished thought_actionos).
    - `thought_action`: Current thought_action (question-task-action) state, typically the latest user query or unfinished interaction.
    """
    """
    Example structure based on DialogueRecord table:
    history is a list of DialogueRecordDTO objects, each containing:
    - id: str
    - conversation_id: str
    - user_id: str
    - user_query: str
    - system_response: str
    - system_thoughts: str | None
    - image_list: list[str] | None
    - query_sent_at: str | None
    - response_received_at: str | None
    - created_at: str | None    

    history also can be a list of dicts in openai format:
    [   
        {"role": "user", "content": "用户说的话"},
        {"role": "assistant", "content": "助手回复", "system_thoughts": "...", "images": [...]}
    ]   

    context is a list of dict objects, for making dao to save to database:
    

    """
    def __init__(self, user_id: str, conversation_id:str,
                 record_business: DialogueRecordBusiness,
                 prompt_template: str,
                 tools_description: str,
                 tools_names: list[str],
                 patient: int = 3):
        if user_id is None or user_id == "":
            raise ValueError("user_id cannot be None or empty")
        self.__user_id = user_id
        self.__user_info = UserInfo(user_id)
        if conversation_id is None or conversation_id == "":
            raise ValueError("conversation_id cannot be None or empty")
        self.__conversation_id = conversation_id

        self.__dependency_record_bussiness = record_business

        self.__is_new_context_available = True
        self.looper = Looper(patient)
        self.__loop_count = 0
        self.__loop_break = False

        self.__query = ""
        self.__query_sent_at = None
        self.__prompt_template = prompt_template
        self.__tools_description = tools_description
        self.__tools_names = tools_names

        self.__context: list[dict] = [] # a list of thought_action_observations, each mapping to a DialogueRecord row.
        self.__thought_action: dict = {}
        self.__final_answer = {}



    @property
    def __load_history_DTO(self) -> list:
        """
        加载对话历史记录 DTO（从数据库）
        :return: 对话历史记录 DTO 列表
        """
        try:
            history = self.__dependency_record_bussiness.list_records_by_conversation(self.__conversation_id, last_n=10)
        except LookupError as e:
            # 如果没有找到记录，返回空列表
            return []
        return history

    def __load_history(self) -> list[dict]:
        """
        加载对话历史记录
        :return: 对话历史记录列表
        """
        history = self.__load_history_DTO
        if not history:
            return []
        
        # 将DTO转换为字典列表
        return [msg    for record in history    for msg in record.to_json()]


    def __push_to_history(self):
        """
        将当前对话上下文推送到历史记录中,
        history 被保存在数据库中，而不是内存
        """
        self.__dependency_record_bussiness.create_record(
            conversation_id=self.__conversation_id,
            user_id=self.__user_id,
            user_query=self.__query,
            query_sent_at=self.__query_sent_at,
            system_response=self.__final_answer.get("answer", ""),
            system_thoughts=self.__load_dumped_context(),
            image_list=self.__final_answer.get("picture", []),
            response_received_at=datetime.datetime.now().isoformat()
        )

    def __load_dumped_context(self) -> str:
        """
        加载已保存的对话上下文
        :return: 对话上下文字符串
        """
        # 这里可以实现从文件或数据库加载已保存的上下文
        # 目前返回一个空字符串作为示例
        return json.dumps(self.__context, ensure_ascii=False, indent=4)
    
    def __start_context(self):
        """
        初始化对话上下文
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def __push_to_context(self):
        """
        设置对话上下文
        """
        self.__context.append(self.__thought_action)
    
    def __close_context(self):
        """
        关闭对话上下文
        """

        self.__context.append({"thought": self.__final_answer.get("thought", "")})

    def __start_thought_action_parse_text_and_save(self, raw_thought_action: str):
        """
        初始化thought_action状态
        :param thought_action: thought_action状态字典
        """
        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.*?)\s*Action:", raw_thought_action, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 提取 Action
        action_match = re.search(r"Action:\s*(.*?)\s*Action Input:", raw_thought_action, re.DOTALL)
        action = action_match.group(1).strip() if action_match else ""

        # 提取 Action Input
        input_match = re.search(r"Action Input:\s*(.*)", raw_thought_action, re.DOTALL)
        action_input = input_match.group(1).strip() if input_match else ""
        # 更稳健的解析
        if isinstance(action_input, dict):
            parsed_input = action_input
        else:
            # 先尝试直接解析
            try:
                parsed_input = json.loads(action_input)
            except Exception:
                # 空字符串或空对象
                if action_input == "" or action_input == "{}":
                    parsed_input = {}
                # 尝试正则提取 json
                elif isinstance(action_input, str):
                    match = re.search(r"{.*}", action_input.strip(), re.DOTALL)
                    if match:
                        try:
                            parsed_input = json.loads(match.group(0))
                        except Exception:
                            parsed_input = match.group(0)
                    else:
                        parsed_input = action_input
                else:
                    parsed_input = str(action_input)
        self.__thought_action = {
            "thought": thought,
            "action": action,
            "action_input": parsed_input,
            "observation": "",
            "raw": raw_thought_action
        }
    
    def __close_thought_action(self, observation: str):
        """
        关闭thought_action状态, push到context
        """
        self.__thought_action["observation"] = observation
        try:
            old_raw = self.__thought_action["raw"]
        except KeyError as e:
            old_raw = ""
        self.__thought_action["raw"] = old_raw + "\nObservation: " + observation

    def __set_final_answer(self, raw_final_answer: str):
        """
        设置最终答案
        :param final_answer: 最终答案字符串
        """
  
        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.*?)\s*Final Answer:", raw_final_answer, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 提取 Final Answer JSON
        answer_str = raw_final_answer.split("Final Answer:")[-1].strip()
        try:
            parsed_answer = json.loads(answer_str)
            answer = parsed_answer.get("answer", "对不起，我无法提供有效的回答。")
            picture = parsed_answer.get("picture", [])
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析最终答案: {e}")

        self.__final_answer = {
            "thought": thought,
            "answer": answer,
            "picture": picture
        }

    def _is_containning_final_answer(self, raw_actions_or_answer) -> bool:
        """
        检查是否处于完成状态
        :return: True if the state is finishing, False otherwise
        """
        if "Final Answer" in raw_actions_or_answer:
            return True

        try:
            # 尝试解析为 JSON
            json.loads(raw_actions_or_answer)
            return True
        except json.JSONDecodeError:
            # 如果解析失败，则不是完成状态
            return False

    def _start_context(self, query: str):
        """
        启动对话上下文
        """
        self.__query = query
        self.__query_sent_at= datetime.datetime.now()
        # todo： 应该加一个锁， 如果已经有上下文了，就不再启动新的上下文
        self.__context = []  # 清空上下文
    
    def _start_thought_action(self, raw_thought_action: str):
        """
        启动thought_action状态
        :param raw_thought_action: 原始thought_action状态字符串
        """
        self.__start_thought_action_parse_text_and_save(raw_thought_action)
    
    def _close_thought_action_and_push_context(self, observation: str):
        """
        关闭thought_action状态并将其推送到上下文
        """
        self.__close_thought_action(observation)
        self.__push_to_context()

    def _set_final_answer_close_context_and_push_history(self, raw_final_answer: str):
        """
        设置最终答案，关闭上下文并将其推送到历史记录
        :param final_answer: 最终答案字符串
        """

        self.__set_final_answer(raw_final_answer)
        self.__close_context()
        self.__push_to_history()
    
    def handle_user_query(self, user_query: str):
        """
        处理用户查询, 有时候会是用户的追答
        :param user_query: 用户查询字符串
        """
        self._start_context(query=user_query)
        
        self.looper.reset()


    def handle_llm_response_and_try_to_stop(self, response: str):
        """
        处理LLM的响应, 要不然start—thought_action， 要不然close-context
        :param response: LLM的响应字符串
        """
        if self._is_containning_final_answer(response):
            self._set_final_answer_close_context_and_push_history(response)
            self.looper.break_loop()
        else:  
            # thought_action 的原始状态不关注，直接覆盖
            self._start_thought_action(response)
    
    def handle_observation(self, observation: str):
        """
        处理观察结果
        :param observation: 观察结果字符串
        """
        self._close_thought_action_and_push_context(observation)
    
    def generate_history_with_context_and_prompt(self, is_containing_prompt = True) -> list:
        """
        生成查询字符串以供LLM使用
        :return: 查询字符串
        """
        history = self.__load_history()

        contexts = [idx.get("raw") for idx in self.__context]
        contexts_str = self.__query + "\n".join(json.dumps(c, ensure_ascii=False) for c in contexts if c is not None)
        if is_containing_prompt:
            contexts_str = self._load_prompt_template() + contexts_str

        new_message = {
            "role": "user",
            "content": contexts_str
        }
        history.append(new_message)
        return history

    def generate_final_answer(self) -> dict:
        """
        生成最终答案
        :return: 最终答案字符串
        """
        # modify the final answer to return a dictionary

        #todo: redefine finalans
        ans = {
            "system_response": self.__final_answer.get("answer", ""),
            "system_thoughts": self.__load_dumped_context(),
            "image_list": self.__final_answer.get("picture", [])
        }

        return ans
    
    def generate_action_input_for_tools(self) -> tuple[str, dict]:
        """
        生成工具的输入参数
        :return: 工具输入参数字典
        """
        return (
            self.__thought_action.get("action", ""),
            self.__thought_action.get("action_input", {})
        )
    
    def _load_prompt_template(self) -> str:
        """
        加载提示模板
        :return: 提示模板字符串
        """
        return self.__prompt_template.format(
            str_tool_description=self.__tools_description,
            date=str(datetime.datetime.now()),  # Example of adding a timestamp
            tool_names=", ".join(self.__tools_names)  # Example of adding tool names
        )