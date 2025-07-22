import os, sys
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if os.path.split(PATH_TO_ROOT)[-1] != "backend":
    raise RuntimeError(f"The root path's last folder must be 'backend'. the path is {PATH_TO_ROOT}")
sys.path.insert(0, PATH_TO_ROOT)
from src.modules.dbController.basis.dbSession import DataBaseSession
from src.modules.dbController.dataModels import User, Conversation, DialogueRecord

from typing import Optional, Dict, Any
from contextlib import contextmanager

# Import DataBaseSession from its module


import logging

logger = logging.getLogger(__name__)

class DatabaseController:
    """
    Database Controller for managing database sessions and operations.
    """

    def __init__(self, config: Dict[str, Any], is_regenerating_table: bool) -> None:
        """
        Initialize the DatabaseController with configuration and table regeneration flag.
        """
        logger.info("Initializing DatabaseController...")
        self.__db_session_manager = DataBaseSession(config, is_regenerating_table)

    """
    user management methods
    """
    def create_user(self, user: User) -> User:
        """
        Create a new user in the database.
        Args:
            user (User): The user object to create.
        Returns:
            User: The created user object.

        raises:
            LookupError: If a user with the same username or ID already exists.
            Exception: If there is an error during user creation.
        """
        try:
            existed = self.get_a_user_by_id(user.id)
            if existed:
                raise RuntimeError(f"User with ID {user.id} already exists.")
        
        except RuntimeError as e:
            logger.warning(f"User exist as hard deleted user: {e}")
            raise LookupError(f"User with ID {user.id} already exists(hard-deleted).") from e
        
        except ValueError as e:
            logger.warning(f"User exist as soft deleted user: {e}")
            # User does not exist, proceed to create
            raise LookupError(f"User with ID {user.id} already exists(soft-deleted).") from e

        except LookupError:
            pass
        
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise Exception(f"Error creating user: {e}")
        
        with self.__db_session_manager.get_session() as session:
                session.add(user)
                session.commit()
                logger.info(f"User created successfully: {user}")
        return self.get_a_user_by_id(user.id)
        

    def update_user(self, user: User) -> User:
        """
        Update an existing user in the database.
        Args:
            user (User): The user object with updated information.
        Returns:
            User: The updated user object.
        raises:
            ValueError: If the user is not found.
            AttributeError: If there is a conflict with existing data.
            Exception: If there is an error during user update.
        """

        with self.__db_session_manager.get_session() as session:
            try:
                existing_user = session.query(User).filter(User.id == user.id).first()

                if not existing_user:
                    raise ValueError(f"User with ID {user.id} not found.")

                for key, value in user.__dict__.items():
                    if key in ['id', '_sa_instance_state']:
                        continue
                    if key == "email":
                        # 检查 email 是否唯一
                        conflict_user = session.query(User).filter(User.email == value, User.id != user.id).first()
                        if conflict_user:
                            raise AttributeError(f"Email '{value}' is already used by another user.")
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

    def __del__update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> User:
        """
        Update user preferences in the database.
        Args:
            user_id (str): The ID of the user whose preferences are to be updated.
            preferences (Dict[str, Any]): The new preferences to set.
        Returns:
            User: The updated user object with new preferences.
        raises:
            ValueError: If the user is not found.
            Exception: If there is an error during preference update.
        """
        with self.__db_session_manager.get_session() as session:
            try:
                user = session.query(User).filter(User.id == user_id).first()
                

                if not user:
                    raise ValueError(f"User with ID {user_id} not found.")
                # Serialize preferences dictionary to JSON string before storing
                import json

                new_preferences = user.user_preferences
                # merge new preferences with old ones
                if new_preferences:
                    new_preferences.update(preferences)
                else:
                    new_preferences = preferences
                user.preferences = json.dumps(new_preferences)
                session.commit()
                logger.info(f"User preferences updated successfully for user ID {user_id}.")
                return user
            
            except ValueError as e:
                logger.error(f"User not found for updating preferences: {e}")
                session.rollback()
                raise ValueError(f"User with ID {user_id} not found.")
            except Exception as e:
                logger.error(f"Error updating user preferences: {e}")
                session.rollback()
                raise

    def get_a_user_by_id(self, user_id: str) -> User:
        """
        Retrieve a user by their ID.
        Args:
            user_id (int): The ID of the user to retrieve.
        Returns:
            User: The user object if found.
        raises:
            LookupError: If the user is not found.
            ValueError: If the user is marked as removed.
        """
        with self.__db_session_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            # check if user is found
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
        Retrieve a user by their username.
        Args:
            username (str): The username of the user to retrieve.
        Returns:
            User: The user object if found.
        raises:
            LookupError: If the user is not found.
            ValueError: If the user is marked as removed.

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

    def delete_user(self, user_id: str, is_hard_delete: bool=False) -> None:
        """
        Delete a user from the database by their ID.
        Args:
            user_id (int): The ID of the user to delete.
            is_hard_delete (bool): Flag indicating whether to perform a hard delete.
        Returns:
            None
        raises:
            LookupError: If the user is not found.
            Exception: If there is an error during user deletion.
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
                    logger.error(f"Error deleting user: {e}")
                    raise
        try:
            with self.__db_session_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    # Bulk soft-delete all conversations
                    session.query(Conversation).filter(Conversation.user_id == user_id).update({"is_removed": True})
                    # Bulk soft-delete all dialogue records related to user's conversations
                    session.query(DialogueRecord).filter(DialogueRecord.conversation_id.in_(session.query(Conversation.id).filter(Conversation.user_id == user_id))).update({"is_removed": True}, synchronize_session=False)
                    # Soft-delete the user
                    user.is_removed = True
                    session.commit()
                    logger.info(f"User with ID {user_id} marked as removed successfully.")
                else:
                    raise ValueError(f"User with ID {user_id} not found.")
        except ValueError as e:
            logger.error(f"User not found for deletion: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise

    """
    conversation management methods
    """
    def create_conversation(self, conversation: Conversation) -> Conversation:
        """
        Create a new conversation in the database.
        Args:
            conversation (Conversation): The conversation object to create.
        Returns:
            Conversation: The created conversation object.
        raises:
            LookupError: If a conversation with the same ID already exists.
            Exception: If there is an error during conversation creation.
        """
        with self.__db_session_manager.get_session() as session:
            try:
                # Check if user exists before creating conversation
                user_exists = session.query(User).filter(User.id == conversation.user_id).first()
                if not user_exists:
                    raise ValueError(f"User with ID {conversation.user_id} does not exist. Cannot create conversation.")
                if conversation.id is not None:
                    existing_conversation = session.query(Conversation).filter(Conversation.id == conversation.id).first()
                    if existing_conversation:
                        raise LookupError(f"Conversation with ID {conversation.id} already exists.")
                session.add(conversation)
                session.commit()
                logger.info(f"Conversation created successfully: {conversation}")
                if conversation.id is None:
                    raise ValueError("Conversation ID cannot be automatically generated.")
                return conversation
                
            
            except LookupError as e:
                logger.error(f"Conversation creation failed: {e}")
                session.rollback()
                raise
            
            except Exception as e:
                logger.error(f"Error creating conversation: {e}")
                session.rollback()
                raise
        
    def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by its ID.
        Args:
            conversation_id (str): The ID of the conversation to retrieve.
        Returns:
            Optional[Conversation]: The conversation object if found, otherwise None.
        raises:
            LookupError: If the conversation is not found.
            ValueError: If the conversation is marked as removed.
        """
        with self.__db_session_manager.get_session() as session:
            conversation = session.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conversation:
                logger.warning(f"Conversation not found with ID: {conversation_id}")
                raise LookupError(f"Conversation with ID {conversation_id} not found.")
            if conversation.is_removed:
                logger.warning(f"Conversation with ID {conversation_id} is marked as removed.")
                raise ValueError(f"Conversation with ID {conversation_id} is marked as removed.")
            return conversation
        
    def update_conversation(self, conversation: Conversation) -> Conversation:
        """
        Update an existing conversation in the database.
        Args:
            conversation (Conversation): The conversation object with updated information.
        Returns:
            Conversation: The updated conversation object.
        raises:
            ValueError: If the conversation is not found.
            Exception: If there is an error during conversation update.
        """
        with self.__db_session_manager.get_session() as session:
            try:
                existing_conversation = session.query(Conversation).filter(Conversation.id == conversation.id).first()

                if not existing_conversation:
                    raise ValueError(f"Conversation with ID {conversation.id} not found.")

                for key, value in conversation.__dict__.items():
                    if key in ['id', '_sa_instance_state']:
                        continue
                    setattr(existing_conversation, key, value)
                session.commit()
                logger.info(f"Conversation updated successfully: {existing_conversation}")
                return existing_conversation
            
            except ValueError as e:
                logger.error(f"Conversation not found for update: {e}")
                session.rollback()
                raise
            
            except Exception as e:
                logger.error(f"Error updating conversation: {e}")
                session.rollback()
                raise

    def delete_conversation(self, conversation_id: str, is_hard_delete: bool = False) -> None:
        """
        Delete a conversation from the database by its ID, and cascade soft-delete all related dialogue records.
        Args:
            conversation_id (str): The ID of the conversation to delete.
            is_hard_delete (bool): Flag indicating whether to perform a hard delete.
        raises:
            LookupError: If the conversation is not found.
            Exception: If there is an error during conversation deletion.
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
                    # Bulk soft-delete all related dialogue records
                    session.query(DialogueRecord).filter(DialogueRecord.conversation_id == conversation_id).update({"is_removed": True}, synchronize_session=False)
                    # Soft-delete the conversation itself
                    session.query(Conversation).filter(Conversation.id == conversation_id).update({"is_removed": True})
                    session.commit()
                logger.info(f"Conversation with ID {conversation_id} marked as removed successfully.")
            else:
                raise ValueError(f"Conversation with ID {conversation_id} not found.")
        except ValueError as e:
            logger.error(f"Conversation not found for deletion: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise

    """
    dialogue record management methods
    """
    def get_record_by_record_id(self, record_id: str) ->DialogueRecord:
        """
        Retrieve a dialogue record by its ID.
        Args:
            record_id (str): The ID of the dialogue record to retrieve.
        Returns:
            Optional[DialogueRecord]: The dialogue record object if found, otherwise None.
        raises:
            LookupError: If the dialogue record is not found.
            ValueError: If the dialogue record is marked as removed.
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
        Create a new dialogue record in the database.
        Args:
            record (DialogueRecord): The dialogue record object to create.
        Returns:
            DialogueRecord: The created dialogue record object.
        raises:
            ValueError: If the record ID is not provided or cannot be automatically generated.
            LookupError: If a dialogue record with the same ID already exists.
            Exception: If there is an error during dialogue record creation.
        """
        with self.__db_session_manager.get_session() as session:
            try:
                # Check if conversation exists
                conversation_exists = session.query(Conversation).filter(Conversation.id == record.conversation_id).first()
                if not conversation_exists:
                    raise ValueError(f"Conversation with ID {record.conversation_id} does not exist. Cannot create dialogue record.")
                # Check if user exists
                user_exists = session.query(User).filter(User.id == record.user_id).first()
                if not user_exists:
                    raise ValueError(f"User with ID {record.user_id} does not exist. Cannot create dialogue record.")
                if record.id is not None:
                    existing_record = session.query(DialogueRecord).filter(DialogueRecord.id == record.id).first()
                    if existing_record:
                        raise LookupError(f"Dialogue record with ID {record.id} already exists.")
                # Ensure conversation_id is not None
                if not getattr(record, 'conversation_id', None):
                    raise ValueError("DialogueRecord.conversation_id cannot be None.")
                session.add(record)
                session.commit()
                logger.info(f"Dialogue record created successfully: {record}")
                if record.id is None:
                    raise ValueError("Dialogue Record ID cannot be automatically generated.")
                return record
                
            
            except LookupError as e:
                logger.error(f"Dialogue Record creation failed: {e}")
                session.rollback()
                raise
            
            except Exception as e:
                logger.error(f"Error creating Dialogue Record: {e}")
                session.rollback()
                raise
    
    def update_dialogue_record(self, record: DialogueRecord) -> DialogueRecord:
        """
        Update an existing dialogue record in the database.
        Args:
            record (DialogueRecord): The dialogue record object with updated information.
        Returns:
            DialogueRecord: The updated dialogue record object.
        raises:
            ValueError: If the dialogue record is not found.
            Exception: If there is an error during dialogue record update.
        """
        with self.__db_session_manager.get_session() as session:
            try:
                existing_record = session.query(DialogueRecord).filter(DialogueRecord.id == record.id).first()

                if not existing_record:
                    raise ValueError(f"Dialogue Record with ID {record.id} not found.")

                for key, value in record.__dict__.items():
                    if key in ['id', '_sa_instance_state']:
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
        Delete a dialogue record from the database by its ID.
        Args:
            record_id (str): The ID of the dialogue record to delete.
            is_hard_delete (bool): Flag indicating whether to perform a hard delete.
        raises:
            LookupError: If the dialogue record is not found.
            Exception: If there is an error during dialogue record deletion.
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
        # soft-delete
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

    def get_records_by_conversation_id(self, conversation_id: str) -> list[DialogueRecord]:
        """
        Retrieve all dialogue records associated with a specific conversation ID.
        Args:
            conversation_id (str): The ID of the conversation to retrieve records for.
        Returns:
            list[DialogueRecord]: A list of dialogue record objects associated with the conversation.
        raises:
            LookupError: If no dialogue records are found for the given conversation ID.
        """
        with self.__db_session_manager.get_session() as session:
            records = session.query(DialogueRecord).filter(DialogueRecord.conversation_id == conversation_id).all()
            filtered_records = [record for record in records if not record.is_removed]
            if not filtered_records:
                logger.warning(f"No dialogue records found for conversation ID: {conversation_id}")
                raise LookupError(f"No dialogue records found for conversation ID {conversation_id}.")
            return filtered_records

