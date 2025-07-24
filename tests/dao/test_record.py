import unittest, sys, os
import logging
import copy  # 添加深拷贝支持
logger = logging.getLogger(__name__)
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, PATH_TO_ROOT)
from src.modules.dbController.dataModels import User, Conversation, DialogueRecord
from src.modules.dao.user_dao import UserDAO
from src.modules.dao.conversation_dao import ConversationDAO
from src.modules.dao.dialogue_record_dao import DialogueRecordDAO
from src.modules.dbController.basis.dbSession import DatabaseSessionManager as DM

from config.loadConfig import ConfigLoader
from datetime import datetime
class TestDataBaseController(unittest.TestCase):
    def setUp(self):
        self.config = ConfigLoader(os.path.join(PATH_TO_ROOT, "config", "config.yaml"))
        self.cvDao = ConversationDAO(DM(self.config.get_db_config()))
        # 只保留一个用户
        self.test_user = User(username="testuser233", id="233333", password_hash="dummyhash", email="testuser@example.com")
        self.test_user_dao = UserDAO(DM(self.config.get_db_config()))
        try:
            self.test_user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        self.test_user = self.test_user_dao.create_user(self.test_user)

        # 创建会话
        self.test_conversation = Conversation(session_name="test_session", user_id=self.test_user.id)
        try:
            self.cvDao.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        try:
            self.test_conversation = self.cvDao.create_conversation(copy.deepcopy(self.test_conversation))  # 使用深拷贝
        except Exception:
            pass
        self.rcDao = DialogueRecordDAO(DM(self.config.get_db_config()))
        self.test_record2_args = dict(user_id=self.test_user.id, user_query="How are you?", system_response="I'm fine, thank you!", query_sent_at=datetime.utcnow())
    
    def test_create_dialogue_record(self):
        # 确保对话记录不存在
        try:
            self.rcDao.delete_dialogue_record(str(self.test_record2_args['user_id']), is_hard_delete=True)
        except Exception:
            pass

        try:
            self.cvDao.delete_conversation(str(self.test_conversation.id), is_hard_delete=True)
        except Exception:
            pass
        self.test_conversation=self.cvDao.create_conversation(self.test_conversation)
        
        # 创建对话记录
        self.assertIsNotNone(self.test_conversation.id)
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(self.test_conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))
        self.assertIsNotNone(created_record)
        self.assertEqual(created_record.user_query, self.test_record2_args['user_query'])

        # 测试对话记录已存在
        with self.assertRaises(LookupError):
            self.rcDao.create_dialogue_record(created_record)
        
        # 测试对话记录已存在，但软删除
        self.rcDao.delete_dialogue_record(created_record.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.rcDao.create_dialogue_record(created_record)
        
        # 测试会话不存在
        record.conversation_id = "non_existent_conversation"
        with self.assertRaises(ValueError):
            self.rcDao.create_dialogue_record(copy.deepcopy(record))
    
    def test_get_record_by_record_id(self):
        # 确保对话记录存在
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(self.test_conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))

        # 查询对话记录
        fetched_record = self.rcDao.get_record_by_record_id(created_record.id)
        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record.user_query, self.test_record2_args['user_query'])

        # 测试查询不存在的对话记录
        with self.assertRaises(LookupError):
            self.rcDao.get_record_by_record_id("non_existent_record")
        
        # 测试软删除的对话记录
        self.rcDao.delete_dialogue_record(created_record.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.rcDao.get_record_by_record_id(created_record.id)
        
    def test_update_dialogue_record(self):
        # 确保对话记录存在
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(self.test_conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))

        # 更新对话记录
        created_record.user_query = "Updated query"
        updated_record = self.rcDao.update_dialogue_record(created_record)
        self.assertIsNotNone(updated_record)
        self.assertEqual(updated_record.user_query, "Updated query")

        # 测试更新不存在的对话记录
        with self.assertRaises(ValueError):
            self.rcDao.update_dialogue_record(DialogueRecord(id="non_existent_id"))

    def test_delete_dialogue_record(self):
        # 确保对话记录存在
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(self.test_conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))

        # 硬删除对话记录
        self.rcDao.delete_dialogue_record(created_record.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.rcDao.get_record_by_record_id(created_record.id)

        # 软删除对话记录
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(self.test_conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))
        self.rcDao.delete_dialogue_record(created_record.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.rcDao.get_record_by_record_id(created_record.id)
    
    def test_get_records_by_conversation_id(self):
        # 确保对话记录存在
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(self.test_conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))

        # 获取会话的所有对话记录
        records = self.rcDao.get_records_by_conversation_id(self.test_conversation.id)
        self.assertIsInstance(records, list)
        self.assertGreater(len(records), 0)
        self.assertEqual(records[0].id, created_record.id)

        # 测试获取不存在的会话的对话记录
        with self.assertRaises(LookupError):
            self.rcDao.get_records_by_conversation_id("non_existent_conversation")
    
    def test_cascade_delete_user(self):
        # 确保用户存在
        try:
            self.test_user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.test_user_dao.create_user(copy.deepcopy(self.test_user))
        self.assertIsNotNone(user)
        # 确保会话存在
        try: 
            self.cvDao.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        conversation = self.cvDao.create_conversation(copy.deepcopy(self.test_conversation))
        # 创建对话记录
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))

        # 硬删除用户
        self.test_user_dao.delete_user(user.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.rcDao.get_record_by_record_id(created_record.id)
        with self.assertRaises(LookupError):
            self.cvDao.get_conversation_by_id(conversation.id)
        
        # 软删除用户
        # 确保用户存在
        try:
            self.test_user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.test_user_dao.create_user(copy.deepcopy(self.test_user))
        self.assertIsNotNone(user)
        # 确保会话存在
        try: 
            self.cvDao.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        conversation = self.cvDao.create_conversation(copy.deepcopy(self.test_conversation))
        # 创建对话记录
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))
        user = self.test_user_dao.get_user_by_id(self.test_user.id)
        self.test_user_dao.delete_user(user.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.rcDao.get_record_by_record_id(created_record.id)
        with self.assertRaises(ValueError):
            self.cvDao.get_conversation_by_id(conversation.id)  
    
    def test_cascade_delete_conversation(self):
        try:
            self.test_user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.test_user_dao.create_user(copy.deepcopy(self.test_user))
        self.assertIsNotNone(user)
        # 确保会话存在
        try: 
            self.cvDao.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        conversation = self.cvDao.create_conversation(copy.deepcopy(self.test_conversation))
        # 创建对话记录
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))

        # 硬删除会话
        self.cvDao.delete_conversation(conversation.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.rcDao.get_record_by_record_id(created_record.id)

        # 软删除会话
        try:
            self.test_user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.test_user_dao.create_user(copy.deepcopy(self.test_user))
        self.assertIsNotNone(user)
        # 确保会话存在
        try: 
            self.cvDao.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        conversation = self.cvDao.create_conversation(copy.deepcopy(self.test_conversation))
        # 创建对话记录
        record = DialogueRecord(**copy.deepcopy(self.test_record2_args), conversation_id=copy.deepcopy(conversation.id))
        created_record = self.rcDao.create_dialogue_record(copy.deepcopy(record))

        self.cvDao.delete_conversation(conversation.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.rcDao.get_record_by_record_id(created_record.id)
        with self.assertRaises(ValueError):
            self.cvDao.get_conversation_by_id(conversation.id)