from src.modules.dbController.dao.conversation_dao import ConversationDAO
from src.modules.dbController.models.conversation import Conversation
from src.modules.services.dto.dto import ConversationDTO
from typing import List

class ConversationBusiness:
    def __init__(self, conversation_dao: ConversationDAO):
        self.conversation_dao = conversation_dao

    def create_conversation(self, user_id: str, session_name: str | None = None) -> ConversationDTO:
        """
        创建新的会话。
        :param user_id: 用户ID
        :param session_name: 会话名称（可选）
        :return: ConversationDTO 对象
        :raises ValueError: 用户ID为空时抛出或参数非法
        :raises LookupError: 用户或会话已存在等业务冲突
        :raises AttributeError: DAO 层属性错误
        :raises Exception: 其它数据库或系统异常
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required.")
        conversation = Conversation(
            user_id=user_id,
            session_name=session_name
        )
        try:
            conversation = self.conversation_dao.create_conversation(conversation)
        except (LookupError, ValueError, AttributeError) as e:
            raise e
        return ConversationDTO.from_obj(conversation)

    def get_conversation(self, conversation_id: str) -> ConversationDTO:
        """
        获取指定会话详情。
        :param conversation_id: 会话ID
        :return: ConversationDTO 对象
        :raises LookupError: 会话不存在
        :raises Exception: 其它数据库或系统异常
        """
        conversation = self.conversation_dao.get_conversation_by_id(conversation_id)
        return ConversationDTO.from_obj(conversation)

    def update_conversation(self, conversation_id: str, session_name: str) -> ConversationDTO:
        """
        更新会话名称。
        :param conversation_id: 会话ID
        :param session_name: 新的会话名称
        :return: ConversationDTO 对象
        :raises LookupError: 会话不存在
        :raises ValueError: 新名称非法
        :raises Exception: 其它数据库或系统异常
        """
        conversation = self.conversation_dao.get_conversation_by_id(conversation_id)
        conversation.session_name = session_name
        conversation = self.conversation_dao.update_conversation(conversation)
        return ConversationDTO.from_obj(conversation)

    def delete_conversation(self, conversation_id: str) -> None:
        """
        删除指定会话。
        :param conversation_id: 会话ID
        :raises LookupError: 会话不存在
        :raises Exception: 其它数据库或系统异常
        """
        self.conversation_dao.delete_conversation(conversation_id)

    def list_user_conversations(self, user_id: str) -> List[ConversationDTO]:
        """
        获取指定用户的所有会话列表。
        :param user_id: 用户ID
        :return: ConversationDTO 对象列表
        :raises LookupError: 用户不存在
        :raises Exception: 其它数据库或系统异常
        """
        conversations = self.conversation_dao.get_conversations_by_user_id(user_id)
        return [ConversationDTO.from_obj(conv) for conv in conversations]
