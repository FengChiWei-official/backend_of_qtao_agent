import unittest, sys, os
import logging
import copy  # 添加深拷贝支持
logger = logging.getLogger(__name__)
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, PATH_TO_ROOT)
from src.modules.dbController.dataModels import User, Conversation, DialogueRecord
from src.modules.dao.user_dao import UserDAO
from src.modules.dao.conversation_dao import ConversationDAO
from src.modules.dbController.basis.dbSession import DatabaseSessionManager as DM

from config.loadConfig import ConfigLoader
from datetime import datetime
class TestDataBaseController(unittest.TestCase):
    def setUp(self):
        # 使用sqlite内存数据库，避免真实数据库依赖
        self.config = ConfigLoader(os.path.join(PATH_TO_ROOT, "config", "config.yaml"))
        self.db_controller = ConversationDAO(DM(self.config.get_db_config()))
        # 只保留一个用户
        self.test_user = User(username="testuser233", id="233333", password_hash="dummyhash", email="testuser@example.com")
        self.test_user_dao = UserDAO(DM(self.config.get_db_config()))
        try:
            self.test_user_dao.create_user(self.test_user)
        except Exception:
            pass
        self.test_conversation = Conversation(session_name="test_session", user_id=self.test_user.id)
        self.test_record2_args = dict(user_id=self.test_user.id, user_query="How are you?", system_response="I'm fine, thank you!", query_sent_at=datetime.utcnow())

    def test_create_conversation(self):
        # 确保会话不存在
        try:
            self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        
        # 创建会话
        created_conversation = self.db_controller.create_conversation(self.test_conversation)
        self.assertIsNotNone(created_conversation)
        self.assertEqual(created_conversation.session_name, self.test_conversation.session_name)

        # 测试会话已存在
        with self.assertRaises(LookupError):
            self.db_controller.create_conversation(self.test_conversation)
        
        # 测试会话已存在，但软删除
        self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.db_controller.create_conversation(self.test_conversation)
        
        # user_id不存在
        conversation2 = copy.deepcopy(self.test_conversation)  # 使用深拷贝
        conversation2.user_id = "non_existent_user"
        with self.assertRaises(ValueError):
            self.db_controller.create_conversation(conversation2)
        
        # conversation name 为空 None
        conversation2 = copy.deepcopy(self.test_conversation)  # 再次深拷贝，防止属性污染
        conversation2.user_id = self.test_user.id
        conversation2.session_name = None
        try:
            self.db_controller.delete_conversation(conversation2.id, is_hard_delete=True)
        except Exception:
            pass
        conversation2 = self.db_controller.create_conversation(conversation2)
        self.assertIsNotNone(conversation2)
        self.assertNotEqual(conversation2.session_name, "")
        self.db_controller.delete_conversation(conversation2.id, is_hard_delete=True)  # 清理
        # conversation name 为空 ""
        conversation2 = copy.deepcopy(self.test_conversation)  # 再次深拷贝
        conversation2.user_id = self.test_user.id
        conversation2.session_name = ""
        conversation2 = self.db_controller.create_conversation(conversation2)
        self.assertIsNotNone(conversation2)
        self.assertNotEqual(conversation2.session_name, "")
        self.db_controller.delete_conversation(conversation2.id, is_hard_delete=True)
        
    def test_get_conversation_by_id(self):
        # 确保会话存在且未软删除
        try:
            self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        conversation = self.db_controller.create_conversation(self.test_conversation)

        # 查询会话
        fetched_conversation = self.db_controller.get_conversation_by_id(conversation.id)
        self.assertIsNotNone(fetched_conversation)
        self.assertEqual(getattr(fetched_conversation, "session_name", ""), conversation.session_name)
        self.assertEqual(getattr(fetched_conversation, "user_id", ""), conversation.user_id)

        # 测试会话不存在
        with self.assertRaises(LookupError):
            self.db_controller.get_conversation_by_id("non_existent_id")
        
        # 测试会话已软删除
        self.db_controller.delete_conversation(conversation.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.db_controller.get_conversation_by_id(conversation.id)
        
    def test_delete_conversation(self):
        # 确保会话存在
        try:
            self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        conversation = self.db_controller.create_conversation(self.test_conversation)

        # 硬删除会话
        self.db_controller.delete_conversation(conversation.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.db_controller.get_conversation_by_id(conversation.id)
        
        # 软删除会话
        self.db_controller.create_conversation(self.test_conversation)
        self.db_controller.delete_conversation(conversation.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.db_controller.get_conversation_by_id(conversation.id)

    def test_update_conversation(self):
        # 确保会话存在且未软删除
        try:
            self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        conversation = self.db_controller.create_conversation(self.test_conversation)

        # 更新会话
        conversation.session_name = "updated_session"
        updated_conversation = self.db_controller.update_conversation(conversation)
        self.assertIsNotNone(updated_conversation)
        self.assertEqual(updated_conversation.session_name, "updated_session")

        # 测试会话不存在
        with self.assertRaises(LookupError):
            self.db_controller.update_conversation(Conversation(id="non_existent_id", session_name="test"))

        # 测试用户已软删除
        self.db_controller.delete_conversation(conversation.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.db_controller.update_conversation(conversation)

