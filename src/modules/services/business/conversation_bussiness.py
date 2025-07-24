from src.modules.dbController.dao.conversation_dao import ConversationDAO
from src.modules.dbController.models.conversation import Conversation
from src.modules.services.dto.dto import ConversationDTO
from typing import List

class ConversationBusiness:
    def __init__(self, conversation_dao: ConversationDAO):
        self.conversation_dao = conversation_dao

    def create_conversation(self, user_id: str, session_name: str | None = None) -> ConversationDTO:
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
        conversation = self.conversation_dao.get_conversation_by_id(conversation_id)
        return ConversationDTO.from_obj(conversation)

    def update_conversation(self, conversation_id: str, session_name: str) -> ConversationDTO:
        conversation = self.conversation_dao.get_conversation_by_id(conversation_id)
        conversation.session_name = session_name
        conversation = self.conversation_dao.update_conversation(conversation)
        return ConversationDTO.from_obj(conversation)

    def delete_conversation(self, conversation_id: str) -> None:
        self.conversation_dao.delete_conversation(conversation_id)

    def list_user_conversations(self, user_id: str) -> List[ConversationDTO]:
        # 这里假设DAO有方法 get_conversations_by_user_id
        conversations = self.conversation_dao.get_conversations_by_user_id(user_id)
        return [ConversationDTO.from_obj(conv) for conv in conversations]
