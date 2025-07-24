from dataclasses import dataclass, fields
from typing import Type, TypeVar, Any
import json

T = TypeVar('T', bound='DTO')

@dataclass
class DTO:
    @classmethod
    def from_obj(cls: Type[T], obj: Any, include: list[str] | None = None) -> T:
        """
        自动从对象生成DTO，只包含include指定的字段。
        :param obj: 源对象（如ORM/DAO对象）
        :param include: 需要包含的字段名列表
        :return: DTO实例
        """
        if include is None:
            include = [f.name for f in fields(cls)]
        data = {k: getattr(obj, k, None) for k in include}
        return cls(**data)

# 示例：
@dataclass
class UserDTO(DTO):
    id: str
    username: str
    email: str | None = None
    is_active: bool = True
    last_login: str | None = None

@dataclass
class ConversationDTO(DTO):
    id: str
    user_id: str
    session_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

@dataclass
class DialogueRecordDTO(DTO):
    id: str
    conversation_id: str
    user_id: str
    user_query: str
    system_response: str
    system_thoughts: str | None = None
    image_list: list[str] | None = None
    query_sent_at: str | None = None
    response_received_at: str | None = None
    created_at: str | None = None

    def to_json(self) -> list[dict[str, Any]]:
        """
        返回OpenAI格式的字符串：
        '[{"role": "user", "content": ...}, {"role": "assistant", "content": ..., "system_thoughts": ..., "images": [...] }]' 
        """
        import json
        result = []
        if self.user_query:
            user_msg = {"role": "user", "content": self.user_query}
            result.append(user_msg)
        if self.system_response:
            assistant_msg: dict[str, str | list[str]] = {"role": "assistant", "content": self.system_response}
            if self.system_thoughts:
                assistant_msg["system_thoughts"] = self.system_thoughts
            if self.image_list:
                assistant_msg["images"] = self.image_list
            result.append(assistant_msg)
        return result

    def __repr__(self) -> str:
        return json.dumps(self.to_json(), ensure_ascii=False)


# 用法：
# user_dto = UserDTO.from_obj(user_orm_obj)
# 或指定字段：UserDTO.from_obj(user_orm_obj, include=["id", "username"])