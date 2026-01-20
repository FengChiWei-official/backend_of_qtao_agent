import sys
import json
from datetime import datetime
from src.utils.root_path import get_root_path
if str(get_root_path()) not in sys.path:
    sys.path.append(str(get_root_path()))

from .utils import Looper
from src.modules.services.service_basis.user_info import UserInfo
from ..business.record_bussiness import DialogueRecordBusiness

class State:
    """
    Manages the state of a user.
    Pure data holder and persistence manager.
    Refactored to remove logic.
    """
    def __init__(self, user_id: str, conversation_id:str,
                 record_business: DialogueRecordBusiness,
                 patient: int = 3):
        if not user_id: raise ValueError("user_id cannot be None or empty")
        if not conversation_id: raise ValueError("conversation_id cannot be None or empty")
        
        self.__user_id = user_id
        self.__conversation_id = conversation_id
        self.__record_business = record_business
        self.looper = Looper(patient)
        
        self.__query = ""
        self.__query_sent_at = None
        
        # State data
        self.__context: list[dict] = [] 
        self.__thought_action: dict = {}
        self.__final_answer: dict = {}

    def init_query(self, query: str):
        """初始化一个新的查询状态"""
        self.__query = query
        self.__query_sent_at = datetime.now()
        self.__context = []
        self.__thought_action = {}
        self.__final_answer = {}
        self.looper.reset()

    def get_query(self) -> str:
        return self.__query

    def get_history(self) -> list:
        """从数据库加载历史记录"""
        try:
            history_dtos = self.__record_business.list_records_by_conversation(self.__conversation_id, last_n=10)
            return [msg for record in history_dtos for msg in record.to_json()]
        except LookupError:
            return []

    def get_context(self) -> list:
        """获取当前执行上下文"""
        return self.__context

    def set_thought_action(self, parsed_ta: dict):
        """设置当前的 thought/action 状态"""
        self.__thought_action = parsed_ta

    def get_current_action(self) -> tuple[str, dict]:
        """获取当前的 Action 和 Input"""
        return (
            self.__thought_action.get("action", ""),
            self.__thought_action.get("action_input", {})
        )

    def update_observation(self, observation: str):
        """更新 Observation 并推送到上下文"""
        self.__thought_action["observation"] = observation
        # 更新 raw 字段以便 prompt 使用
        old_raw = self.__thought_action.get("raw", "")
        self.__thought_action["raw"] = old_raw + "\nObservation: " + observation
        
        # Push to context
        self.__context.append(self.__thought_action)
    
    def set_final_answer(self, parsed_answer: dict):
        """设置最终答案"""
        self.__final_answer = parsed_answer
        # 将最终的 thought 推入 context，保留思考痕迹
        self.__context.append({"thought": parsed_answer.get("thought", "")})

    def save_to_db(self, fallback_response: str = None):
        """持久化当前状态到数据库"""
        system_response = self.__final_answer.get("answer", "")
        if not system_response and fallback_response:
             system_response = fallback_response
        
        system_thoughts = json.dumps(self.__context, ensure_ascii=False, indent=4) if self.__context else ""

        self.__record_business.create_record(
            conversation_id=self.__conversation_id,
            user_id=self.__user_id,
            user_query=self.__query,
            query_sent_at=self.__query_sent_at,
            system_response=system_response,
            system_thoughts=system_thoughts,
            image_list=self.__final_answer.get("picture", []),
            response_received_at=datetime.now().isoformat()
        )

    def get_final_result(self) -> dict:
        """获取最终返回给用户的格式化结果"""
        return {
            "system_response": self.__final_answer.get("answer", ""),
            "system_thoughts": json.dumps(self.__context, ensure_ascii=False, indent=4),
            "image_list": self.__final_answer.get("picture", [])
        }
