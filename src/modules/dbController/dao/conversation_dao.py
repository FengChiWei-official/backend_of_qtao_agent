import logging
from src.modules.dbController.models.record import DialogueRecord
from src.modules.dbController.models.conversation import Conversation
from src.modules.dbController.models.user import User
from src.modules.dbController.basis.dbSession import DatabaseSessionManager
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy.orm import make_transient

logger = logging.getLogger(__name__)

class ConversationDAO:
    def __init__(self, config: dict):
        self.__db_session_manager = DatabaseSessionManager(config)

    def create_conversation(self, conversation: Conversation) -> Conversation:
        """
        创建会话
        :param conversation: Conversation对象
        :return: 创建的Conversation对象
        :raises ValueError: 如果用户不存在或会话ID已存在(soft-deleted)
        :raises LookupError: 如果会话已存在
        :raises AttributeError: 如果会话的user_id不存在或已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            if not getattr(conversation, 'user_id', None):
                raise AttributeError("Conversation must have a user_id set.")
            name = getattr(conversation, 'session_name', None)
            if not name or name.strip() == "":
                conversation.session_name = f"session {datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')}"
            user = session.query(User).filter(User.id == conversation.user_id).first()
            if not user:
                raise ValueError(f"User with ID {conversation.user_id} does not exist.")
            if user.is_removed:
                raise ValueError(f"User with ID {conversation.user_id} has been soft-deleted.")
            existing_conversation = session.query(Conversation).filter(Conversation.id == conversation.id).first()
            if existing_conversation:
                if existing_conversation.is_removed:
                    raise ValueError(f"Conversation with ID {conversation.id} has been soft-deleted.")
                else:
                    raise LookupError(f"Conversation with ID {conversation.id} already exists.")
            try:
                # Ensure the conversation object is not attached to another session
                if hasattr(conversation, '_sa_instance_state') and conversation._sa_instance_state.session is not None:
                    conversation._sa_instance_state.session.expunge(conversation)
                make_transient(conversation)  # 强制转为新对象
                session.add(conversation)
                session.commit()
                logger.info(f"Conversation created successfully: {conversation}")
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Conversation with ID {conversation.id} already exists.") from e
            
            if conversation.id is None:
                raise AttributeError("Conversation ID is not set after creation.")
            return conversation

    def get_conversation_by_id(self, conversation_id: str) -> Conversation:
        """
        获取会话
        :param conversation_id: 会话ID
        :return: Conversation对象
        :raises LookupError: 如果会话不存在
        :raises ValueError: 如果会话已被软删除
        :raises ValueError: 如果用户不存在或已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            conversation = session.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conversation:
                logger.warning(f"Conversation not found with ID: {conversation_id}")
                raise LookupError(f"Conversation with ID {conversation_id} not found.")
            if conversation.is_removed:
                logger.warning(f"Conversation with ID {conversation_id} is marked as removed.")
                raise ValueError(f"Conversation with ID {conversation_id} is marked as removed.")
            user = session.query(User).filter(User.id == conversation.user_id).first()
            if not user or user.is_removed:
                logger.warning(f"User not found or soft-deleted for conversation ID: {conversation_id}")
                raise ValueError(f"User for conversation {conversation_id} does not exist or has been soft-deleted.")
            return conversation

    def get_conversations_by_user_id(self, user_id: str) -> list[Conversation]:
        """
        获取用户的所有会话
        :param user_id: 用户ID
        :return: Conversation对象列表
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果用户已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise LookupError(f"User with ID {user_id} not found.")
            if user.is_removed:
                raise ValueError(f"User with ID {user_id} has been soft-deleted.")
            conversations = session.query(Conversation).filter(Conversation.user_id == user_id, Conversation.is_removed == False).all()
            return conversations

    def update_conversation(self, conversation: Conversation) -> Conversation:
        """
        更新会话
        :param conversation: Conversation对象
        :return: 更新后的Conversation对象
        :raises LookupError: 如果会话不存在
        :raises ValueError: 如果会话不存在或用户已被软删除
        :raises ValueError: 如果会话已被软删除
        :raises AttributeError: 如果会话如果存在属性完整性约束冲突
        """
        with self.__db_session_manager.get_session() as session:
            try:
                id = getattr(conversation, 'id', None)
                if not id:
                    raise LookupError(f"New conversation must have an ID to update.")
                existing_conversation = session.query(Conversation).filter(Conversation.id == conversation.id).first()
                if existing_conversation is None:
                    logger.warning(f"Conversation with ID {conversation.id} not found for update.")
                    raise LookupError(f"Conversation with ID {conversation.id} not found.")
                if getattr(existing_conversation, 'is_removed', False):
                    logger.warning(f"Conversation with ID {conversation.id} is marked as removed.")
                    raise ValueError(f"Conversation with ID {conversation.id} is marked as removed.")
                # Update conversation fields
                for key, value in conversation.__dict__.items():
                    if key in ['id', '_sa_instance_state']:
                        logger.warning(f"Skipping key {key} as it should not be updated.")
                        continue
                    setattr(existing_conversation, key, value)
                session.commit()
                logger.info(f"Conversation updated successfully: {existing_conversation}")
                return existing_conversation
            except IntegrityError as e:
                logger.error(f"Integrity error occurred while updating conversation: {e}")
                session.rollback()
                raise AttributeError(f"Conversation with ID {conversation.id} already exists.") from e

    def delete_conversation(self, conversation_id: str, is_hard_delete: bool = False) -> None:
        """
        删除会话
        :param conversation_id: 会话ID
        :param is_hard_delete: 是否硬删除
        :raises LookupError: 如果会话不存在

        """
        if is_hard_delete:
            with self.__db_session_manager.get_session() as session:
                try:
                    conversation = session.query(Conversation).filter(Conversation.id == conversation_id).first()
                    if not conversation:
                        raise LookupError(f"Conversation with ID {conversation_id} not found.")
                    session.delete(conversation)
                    session.commit()
                    logger.info(f"Conversation with ID {conversation_id} deleted successfully.")
                    return
                except Exception as e:
                    session.rollback()
                    logger.error(f"Error deleting conversation: {e}")
                    raise
        try:
            conversation = self.get_conversation_by_id(conversation_id)
            if conversation:
                with self.__db_session_manager.get_session() as session:
                    session.query(DialogueRecord).filter(DialogueRecord.conversation_id == conversation_id).update({"is_removed": True}, synchronize_session=False)
                    session.query(Conversation).filter(Conversation.id == conversation_id).update({"is_removed": True})
                    session.commit()
                logger.info(f"Conversation with ID {conversation_id} marked as removed successfully.")
            else:
                raise LookupError(f"Conversation with ID {conversation_id} not found.")
        except Exception as e:
            logger.error(f"Error marking conversation as removed: {e}")
            raise
