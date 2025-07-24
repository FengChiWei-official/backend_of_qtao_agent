import logging
from src.modules.dbController.models.record import DialogueRecord
from src.modules.dbController.models.conversation import Conversation
from src.modules.dbController.models.user import User
from src.modules.dbController.basis.dbSession import DatabaseSessionManager
from typing import List
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class DialogueRecordDAO:
    def __init__(self, db_session_manager: DatabaseSessionManager):
        self.__db_session_manager = db_session_manager

    def get_record_by_record_id(self, record_id: str) -> DialogueRecord:
        """
        :param record_id: 对话记录ID
        :return: DialogueRecord对象
        :raises LookupError: 如果对话记录不存在
        :raises ValueError: 如果对话记录已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            record = session.query(DialogueRecord).filter(DialogueRecord.id == record_id).first()
            if not record:
                logger.warning(f"Dialogue record not found with ID: {record_id}")
                raise LookupError(f"Dialogue record with ID {record_id} not found.")
            if record.is_removed:
                logger.warning(f"Dialogue record with ID {record_id} is soft-deleted.")
                raise ValueError(f"Dialogue record with ID {record_id} is soft-deleted.")
            return record

    def create_dialogue_record(self, record: DialogueRecord) -> DialogueRecord:
        """
        创建对话记录
        :param record: DialogueRecord对象
        :return: 创建的DialogueRecord对象
        :raises ValueError: 会话或用户不存在，或conversation_id为None
        :raises LookupError: 记录已存在
        """
        with self.__db_session_manager.get_session() as session:
            # 检查会话和用户是否存在
            if not getattr(record, 'conversation_id', None):
                raise ValueError("DialogueRecord.conversation_id cannot be None.")
            if not getattr(record, 'user_id', None):
                raise ValueError("DialogueRecord.user_id cannot be None.")
            conversation_exists = session.query(Conversation).filter(Conversation.id == record.conversation_id).first()
            if not conversation_exists:
                raise ValueError(f"Conversation with ID {record.conversation_id} does not exist. Cannot create dialogue record.")
            user_exists = session.query(User).filter(User.id == record.user_id).first()
            if not user_exists:
                raise ValueError(f"User with ID {record.user_id} does not exist. Cannot create dialogue record.")
            # 检查记录是否已存在
            if record.id is not None:
                existing_record = session.query(DialogueRecord).filter(DialogueRecord.id == record.id).first()
                if existing_record:
                    if existing_record.is_removed:
                        raise ValueError(f"Dialogue record with ID {record.id} has been soft-deleted.")
                    raise LookupError(f"Dialogue record with ID {record.id} already exists.")
            if not getattr(record, 'conversation_id', None):
                raise ValueError("DialogueRecord.conversation_id cannot be None.")
            if not getattr(record, 'user_id', None):
                raise ValueError("DialogueRecord.user_id cannot be None.")
            
            try:
                session.add(record)
                session.commit()
                logger.info(f"Dialogue record created successfully: {record}")
                if record.id is None:
                    raise ValueError("Dialogue Record ID cannot be automatically generated.")
                return record
            except IntegrityError as e:
                session.rollback()
                logger.error(f"Error creating Dialogue Record:完整性约束不能满足 {e}")
                raise

    def update_dialogue_record(self, record: DialogueRecord) -> DialogueRecord:
        """
        更新对话记录
        :param record: DialogueRecord对象
        :return: 更新后的DialogueRecord对象
        :raises ValueError: 如果对话记录不存在
        :raises LookupError: 如果对话记录已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            try:
                existing_record = session.query(DialogueRecord).filter(DialogueRecord.id == record.id).first()
                if not existing_record:
                    raise ValueError(f"Dialogue Record with ID {record.id} not found.")
                for key, value in record.__dict__.items():
                    if key in ['id', '_sa_instance_state']:
                        logger.warning(f"Skipping key {key} as it should not be updated.")
                        continue
                    setattr(existing_record, key, value)
                session.commit()
                logger.info(f"Dialogue Record updated successfully: {existing_record}")
                return existing_record
            except ValueError as e:
                logger.error(f"Dialogue Record not found for update: {e}")
                session.rollback()
                raise
            except Exception as e:
                logger.error(f"Error updating Dialogue Record: {e}")
                session.rollback()
                raise

    def delete_dialogue_record(self, record_id: str, is_hard_delete: bool=False) -> None:
        """
        软或硬删除对话记录
        :param record_id: 对话记录ID
        :param is_hard_delete: 是否硬删除
        :raises LookupError: 如果对话记录不存在
        :raises ValueError: 如果对话记录已被软删除
        """
        if is_hard_delete:
            with self.__db_session_manager.get_session() as session:
                try:
                    record = session.query(DialogueRecord).filter(DialogueRecord.id == record_id).first()
                    if not record:
                        raise LookupError(f"Dialogue Record with ID {record_id} not found.")
                    session.delete(record)
                    session.commit()
                    logger.info(f"Dialogue Record with ID {record_id} deleted successfully.")
                    return
                except LookupError as e:
                    session.rollback()
                    logger.error(f"Dialogue Record not found for deletion: {e}")
                    raise
                except Exception as e:
                    session.rollback()
                    logger.error(f"Error deleting Dialogue Record: {e}")
                    raise
        with self.__db_session_manager.get_session() as session:
            try:
                record = session.query(DialogueRecord).filter(DialogueRecord.id == record_id).first()
                if not record:
                    raise LookupError(f"Dialogue Record with ID {record_id} not found.")
                record.is_removed = True
                session.commit()
                logger.info(f"Dialogue Record with ID {record_id} marked as removed successfully.")
            except LookupError as e:
                session.rollback()
                logger.error(f"Dialogue Record not found for deletion: {e}")
                raise
            except Exception as e:
                session.rollback()
                logger.error(f"Error deleting Dialogue Record: {e}")
                raise

    def get_records_by_conversation_id(self, conversation_id: str, last_n: int | None = None) -> List[DialogueRecord]:
        """
        获取指定会话的所有对话记录
        :param conversation_id: 会话ID
        :return: 对话记录列表
        :raises LookupError: 如果没有找到对话记录
        """
        with self.__db_session_manager.get_session() as session:
            reversed_records = session.query(DialogueRecord).filter(DialogueRecord.conversation_id == conversation_id, DialogueRecord.is_removed == False).order_by(DialogueRecord.created_at.desc()).all()
            if last_n is not None:
                reversed_records = reversed_records[:last_n]
            ordered_dialogue_records = reversed_records[::-1]  # Reverse to maintain chronological order
            if not ordered_dialogue_records:
                logger.warning(f"No dialogue records found for conversation ID: {conversation_id}")
                raise LookupError(f"No dialogue records found for conversation ID {conversation_id}.")
            return ordered_dialogue_records
