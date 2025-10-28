import logging

from sqlalchemy.orm import make_transient

from src.modules.dbController.models.record import DialogueRecord
from src.modules.dbController.models.conversation import Conversation
from src.modules.dbController.models.user import User
from src.modules.dbController.basis.dbSession import DatabaseSessionManager
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class UserDAO:
    def __init__(self, config: dict):
        self.__db_session_manager = DatabaseSessionManager(config)

    def create_user(self, user: User) -> User:
        """ 创建用户
        :param user: User对象
        :return: 创建的User对象 
        :raises LookupError: 如果用户已存在
        :raises ValueError: 用户已经被软删除，无法再次创建
        :raises AttributeError: 如果email或username已被其他用户使用
        """
        with self.__db_session_manager.get_session() as session:
            unique_check = session.query(User).filter(User.id == user.id).first()
            if unique_check is not None:
                if unique_check.is_removed:
                    raise ValueError(f"User with ID {user.id} has been soft-deleted and cannot be recreated.")
                raise LookupError(f"User with ID {user.id} already exists.")
            # Check for username/email uniqueness before attempting insert to provide clearer errors
            if hasattr(user, 'username') and user.username:
                existing_by_username = session.query(User).filter(User.username == user.username).first()
                if existing_by_username is not None:
                    if existing_by_username.is_removed:
                        raise ValueError(f"Username '{user.username}' belongs to a removed user and cannot be reused.")
                    raise LookupError(f"Username '{user.username}' already exists.")
            if hasattr(user, 'email') and user.email:
                existing_by_email = session.query(User).filter(User.email == user.email).first()
                if existing_by_email is not None:
                    if existing_by_email.is_removed:
                        raise ValueError(f"Email '{user.email}' belongs to a removed user and cannot be reused.")
                    raise LookupError(f"Email '{user.email}' already exists.")
            try:
                if hasattr(user, '_sa_instance_state') and user._sa_instance_state.session is not None:
                    user._sa_instance_state.session.expunge(user)
                make_transient(user)  # 强制转为新对象
                session.add(user)
                session.flush()  # 确保ID被分配
            except IntegrityError as e:
                # A race condition may still cause a DB-level unique constraint violation.
                # Map it to LookupError so the handler can return HTTP 409 Conflict.
                session.rollback()
                raise LookupError("Unique attribute conflict, user already exists") from e
            session.commit()
            logger.info(f"User created successfully: {user}")
        return self.get_user_by_id(user.id)

    def update_user(self, user: User) -> User:
        """
        :param user: User对象
        :return: 更新后的User对象
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果用户已被软删除
        :raises AttributeError: 如果更新的email/username已被其他用户使用
        """
        with self.__db_session_manager.get_session() as session:
            try:
                existing_user = session.query(User).filter(User.id == user.id).first()
                if not existing_user:
                    raise ValueError(f"User with ID {user.id} not found.")
                for key, value in user.__dict__.items():
                    if key in ['id', '_sa_instance_state']:
                        logger.warning(f"Skipping key {key} as it should not be updated.")
                        continue
                    if key in ["email", "username"]:
                        conflict_user = session.query(User).filter(getattr(User, key) == value, User.id != user.id).first()
                        if conflict_user:
                            raise AttributeError(f"{key.capitalize()} '{value}' is already used by another user.")
                    setattr(existing_user, key, value)
                session.commit()
                logger.info(f"User updated successfully: {existing_user}")
                return existing_user
            except ValueError as e:
                logger.error(f"User not found for update: {e}")
                session.rollback()
                raise
            except Exception as e:
                logger.error(f"Error updating user: {e}")
                session.rollback()
                raise

    def get_user_by_id(self, user_id: str) -> User:
        """
        :param user_id: 用户ID
        :return: User对象
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果用户已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User not found with ID: {user_id}")
                raise LookupError(f"User with ID {user_id} not found.")
            if user.is_removed:
                logger.warning(f"User with ID {user_id} is marked as removed.")
                raise ValueError(f"User with ID {user_id} is marked as removed.")
            logger.info(f"User found: {user}")
            return user

    def get_user_by_username(self, username: str) -> User:
        """
        :param username: 用户名
        :return: User对象
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果用户已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"User not found with username: {username}")
                raise LookupError(f"User with username {username} not found.")
            if user.is_removed:
                logger.warning(f"User with username {username} is marked as removed.")
                raise ValueError(f"User with username {username} is marked as removed.")
            logger.info(f"User found: {user}")
            return user

    def get_user_by_email(self, email: str) -> User:
        """
        :param email: 用户邮箱
        :return: User对象
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果用户已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                logger.warning(f"User not found with email: {email}")
                raise LookupError(f"User with email {email} not found.")
            if user.is_removed:
                logger.warning(f"User with email {email} is marked as removed.")
                raise ValueError(f"User with email {email} is marked as removed.")
            logger.info(f"User found: {user}")
            return user

    def delete_user(self, user_id: str, is_hard_delete: bool=False) -> None:
        """
        :param user_id: 用户ID
        :param is_hard_delete: 是否进行硬删除
        :raises LookupError: 如果用户不存在
        :raises ValueError: 重复软删除
        """
        if is_hard_delete:
            with self.__db_session_manager.get_session() as session:
                try:
                    user = session.query(User).filter(User.id == user_id).first()
                    if not user:
                        raise LookupError(f"User with ID {user_id} not found.")
                    session.delete(user)
                    session.commit()
                    logger.info(f"User with ID {user_id} deleted successfully.")
                    return
                except LookupError as e:
                    session.rollback()
                    logger.error(f"User not found for deletion: {e}")
                    raise
                except Exception as e:
                    session.rollback()
                    raise
        try:
            with self.__db_session_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    if user.is_removed:
                        raise ValueError(f"User with ID {user_id} not found.")
                    session.query(Conversation).filter(Conversation.user_id == user_id).update({"is_removed": True})
                    session.query(DialogueRecord).filter(DialogueRecord.conversation_id.in_(session.query(Conversation.id).filter(Conversation.user_id == user_id))).update({"is_removed": True}, synchronize_session=False)
                    user.is_removed = True
                    session.commit()
                    logger.info(f"User with ID {user_id} marked as removed successfully.")
                else:
                    raise LookupError(f"User with ID {user_id} not found.")
        except ValueError as e:
            logger.error(f"User already marked as removed: {e}")
            raise

    def check_user_ownership(self, user_id: str, conversation_id: str) -> bool:
        """
        检查用户是否拥有指定会话
        :param user_id: 用户ID
        :param conversation_id: 会话ID
        :return: 如果用户拥有该会话则返回 True，否则返回 False
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果用户已被软删除
        """
        with self.__db_session_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User with ID {user_id} not found or is marked as removed.")
                raise LookupError(f"User with ID {user_id} not found.")
            if user.is_removed:
                logger.warning(f"User with ID {user_id} is marked as removed.")
                raise ValueError(f"User with ID {user_id} is marked as removed.")
            conversation = session.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id, Conversation.is_removed == False).first()
            if not conversation:
                logger.warning(f"Conversation with ID {conversation_id} not found for user {user_id}.")
                return False
            logger.info(f"User {user_id} owns conversation {conversation_id}.")
            return True