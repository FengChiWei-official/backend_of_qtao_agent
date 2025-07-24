from .conversation_dao import ConversationDAO  # Add this import at the top
from .user_dao import UserDAO
from .dialogue_record_dao import DialogueRecordDAO
from src.modules.dbController.basis.dbSession import DatabaseSessionManager

class DAO:
    def __init__(self, db_connection_manager: DatabaseSessionManager):
        self.user_dao = UserDAO(db_connection_manager)
        self.conversation_dao = ConversationDAO(db_connection_manager)
        self.dialogue_record_dao = DialogueRecordDAO(db_connection_manager)


