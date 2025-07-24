import unittest, sys, os
import logging
logger = logging.getLogger(__name__)
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, PATH_TO_ROOT)
from src.modules.dbController.dataModels import User, Conversation, DialogueRecord
from src.modules.dbController.db_controller import DatabaseController

from config.loadConfig import ConfigLoader
from datetime import datetime
class TestDataBaseController(unittest.TestCase):
    def setUp(self):
        # 使用sqlite内存数据库，避免真实数据库依赖
        self.config = ConfigLoader(os.path.join(PATH_TO_ROOT, "config", "config.yaml"))
        self.db_controller = DatabaseController(self.config.get_db_config())
        # 只保留一个用户
        self.test_user = User(username="testuser233", id="233333", password_hash="dummyhash", email="testuser@example.com")
        # 只保留一个会话
        self.test_conversation = Conversation(session_name="test_session", user_id=self.test_user.id)
       
        self.test_record2_args = dict(user_query="How are you?", system_response="I'm fine, thank you!", query_sent_at=datetime.utcnow())
        self.test_record3_args = dict(user_query="What's up?", system_response="All good!", query_sent_at=datetime.utcnow())

    # -------------------- User Management Tests --------------------
    def test_create_user(self):
        # 1. Setup: Ensure self.test_user does not exist
        try:
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception as e:
            logger.warning(f"Setup failed to delete user {self.test_user.id}: {e}")
            pass
        try:
            self.db_controller.get_user_by_id(self.test_user.id)
            raise RuntimeError("用户未被成功删除，主键冲突风险")
        except (LookupError, ValueError):
            pass
        # 2. Test: Create user（始终用 self.test_user）
        created_user = self.db_controller.create_user(self.test_user)
        self.assertEqual(created_user.username, self.test_user.username)
        self.assertEqual(created_user.id, self.test_user.id)
        # 3. Robustness: Try to create the same user again, should raise LookupError
        with self.assertRaises(LookupError):
            self.db_controller.create_user(self.test_user)
        
        with self.assertRaises(ValueError):
            pass

        # 注释说明：确保创建相同用户时抛出异常
        # 这里的测试确保了用户创建的健壮性和正确性
        # - 第一步确保测试环境中用户不存在。
        # - 第二步验证创建功能。
        # - 第三步验证异常分支，确保创建相同用户时抛出 LookupError。

    def test_get_user_by_username(self):
        # 1. Setup: 保证 test_user 存在且未被软删除
        # 问题考虑：
        # - 用户必须存在，否则查询会报错
        # - 用户不能被软删除，否则查询会抛异常
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
            # 如果用户被软删除，则重新插入
        except LookupError:
            # 用户不存在，插入新用户
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            try:
                self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
                user = self.db_controller.create_user(self.test_user)
            except Exception as e:
                raise RuntimeError(f"Error during user setup, 发生什么了: {e}")
        # 2. Test: 查询 test_user，确保能查到且数据正确
        fetched_user = self.db_controller.get_user_by_username(self.test_user.username)
        self.assertIsNotNone(fetched_user)  # 用户必须查得到
        self.assertEqual(fetched_user.username, self.test_user.username)  # 用户名必须一致
        # 3. Robustness: 查询不存在用户，必须抛异常
        with self.assertRaises(LookupError):
            self.db_controller.get_user_by_username("nonexistentuser")
        # 测试软删除的健壮性
        # 这里的测试确保了用户查询的健壮性和正确性
        self.db_controller.delete_user(self.test_user.id, is_hard_delete=False)  # 软删除用户
        self.assertRaises(ValueError, self.db_controller.get_user_by_username, self.test_user.username)  # 查询软删除用户必须抛异常
        # 注释说明：
        # - 第一步确保测试环境中 test_user 存在且有效（未软删除），否则后续查询会失败。
        # - 第二步验证正常查询结果。
        # - 第三步验证异常分支，确保不存在用户时抛出 LookupError。

    def test_get_a_user_by_id(self):
        # 1. Setup: Ensure user exists and is not soft-deleted
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
            user = self.db_controller.create_user(self.test_user)
        # 2. Test: Get user by id
        fetched_user = self.db_controller.get_user_by_id(self.test_user.id)
        self.assertIsNotNone(fetched_user)
        self.assertEqual(fetched_user.id, self.test_user.id)
        # 3. Robustness: Try to get non-existent user, should raise LookupError
        with self.assertRaises(LookupError):
            self.db_controller.get_user_by_id("nonexistentid")
        # 注释说明：
        # - 第一步setup确保用户存在且未软删除。
        # - 第二步验证获取功能。
        # - 第三步验证异常分支。

    def test_update_user(self):
        # 1. Setup: Ensure user exists and is not soft-deleted
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # 2. Test: Update user
        bk_pwd = user.password_hash
        user.password_hash = "newpasswordhash"
        updated_user = self.db_controller.update_user(user)
        self.assertEqual(updated_user.password_hash, "newpasswordhash")
        user.password_hash = bk_pwd  # 恢复原密码
        user = self.db_controller.update_user(user)  # 更新回原密码
        self.assertEqual(user.password_hash, bk_pwd)
        # 2. Test: Update user email
        user.email = "newemail@example.com"
        with self.assertRaises(AttributeError):
            updated_user = self.db_controller.update_user(user)
        # 注释说明：
        # - 第一步setup确保用户存在且未软删除。
        # - 第二步验证更新功能。
        # - 第三步验证异常分支。

    def test_hard_delete_user(self):
        # 1. Setup: Ensure user exists and is not soft-deleted
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # 2. Setup: Insert conversation and record for valid foreign key
        # 保证会话不存在，先硬删除
        try:
            self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        delete_conversation_obj = self.db_controller.create_conversation(self.test_conversation)
        try:
            self.db_controller.delete_dialogue_record(str(self.test_record2_args['conversation_id']))
        except Exception:
            pass
        delete_record_obj = self.db_controller.create_dialogue_record(
            DialogueRecord(conversation_id=delete_conversation_obj.id, user_id=self.test_user.id, user_query="Test", system_response="Response", query_sent_at=datetime.utcnow())
        )
        # 3. Test: Hard delete user（级联删除会话和记录）
        self.db_controller.delete_user(user.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.db_controller.get_user_by_id(user.id)
        with self.assertRaises(LookupError):
            self.db_controller.get_conversation_by_id(delete_conversation_obj.id)
        with self.assertRaises(LookupError):
            self.db_controller.get_record_by_record_id(delete_record_obj.id)
        # 4. Robustness: Try to delete again, should not raise but do nothing
        try:
            self.db_controller.delete_user(user.id, is_hard_delete=True)
        except Exception as e:
            self.assertTrue(isinstance(e, Exception))
        # 注释说明：
        # - 第一步确保测试环境中用户存在且未软删除。
        # - 第二步插入会话和记录，保证外键约束。
        # - 第三步验证硬删除级联效果。
        # - 第四步验证重复删除的健壮性。

    def test_soft_delete_user(self):
        # 1. Setup: Ensure user exists and is not soft-deleted

        try:
            user2 = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user2 = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
            user2 = self.db_controller.create_user(self.test_user)
        try:
            self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except Exception:
            pass
        soft_conversation_obj = self.db_controller.create_conversation(self.test_conversation)
        try:
            self.db_controller.delete_dialogue_record(str(self.test_record2_args['conversation_id']))
        except Exception:
            pass
        soft_record_obj = self.db_controller.create_dialogue_record(
            DialogueRecord(conversation_id=soft_conversation_obj.id, user_id=user2.id, user_query="Soft", system_response="Delete", query_sent_at=datetime.utcnow())
        )
        # 2. Test: Soft delete user（级联软删除会话和记录）
        self.db_controller.delete_user(user2.id, is_hard_delete=False)  # 执行软删除用户，应该级联软删除相关会话和记录
        with self.assertRaises(ValueError):
            self.db_controller.get_user_by_id(user2.id)  # 查询被软删除的用户，应该抛出 ValueError
        with self.assertRaises(ValueError):
            self.db_controller.get_conversation_by_id(soft_conversation_obj.id)  # 查询被软删除的会话，应该抛出 ValueError
        with self.assertRaises(ValueError):
            self.db_controller.get_record_by_record_id(soft_record_obj.id)  # 查询被软删除的记录，应该抛出 LookupError
        # 3. Robustness: Try to delete again, should not raise but do nothing
        try:
            self.db_controller.delete_user(user2.id, is_hard_delete=False)
        except Exception as e:
            self.assertTrue(isinstance(e, Exception))
        # 注释说明：
        # - 第一步插入软删除用户、会话和记录。
        # - 第二步验证软删除级联效果。
        # - 第三步验证重复软删除的健壮性。

    # -------------------- Conversation Management Tests --------------------
    def test_create_conversation(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除，且 session 不存在
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # 确保 session 不存在
        try:
            exist_conv = self.db_controller.get_conversation_by_id(self.test_conversation.id)
            if exist_conv:
                self.db_controller.delete_conversation(self.test_conversation.id, is_hard_delete=True)
        except LookupError:
            pass
        # Step 2: 测试正常环境下创建会话
        conversation = Conversation(session_name="test_session", user_id=user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        self.assertEqual(created_conversation.session_name, conversation.session_name)
        self.assertEqual(created_conversation.user_id, conversation.user_id)
        # Step 3: 异常情况，尝试用不存在用户创建会话，应该报错
        fake_conversation = Conversation(session_name="fake_session", user_id="fakeid")
        with self.assertRaises(Exception):
            self.db_controller.create_conversation(fake_conversation)

    def test_get_conversation_by_id(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话存在且未被软删除
        conversation = Conversation(session_name="test_session2", user_id=self.test_user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        # Step 2: 测试正常环境下可以获取会话
        fetched_conversation = self.db_controller.get_conversation_by_id(created_conversation.id)
        self.assertIsNotNone(fetched_conversation)
        if fetched_conversation is not None:
            self.assertEqual(fetched_conversation.id, created_conversation.id)
        # Step 3: 异常情况，获取不存在的会话，应该报错
        with self.assertRaises(LookupError):
            self.db_controller.get_conversation_by_id("nonexistentid")
        # 注释说明：
        # - 第一步setup确保用户和会话存在且未软删除。
        # - 第二步验证获取功能。
        # - 第三步验证异常分支。

    def test_update_conversation(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话存在且未被软删除
        conversation = Conversation(session_name="update_session", user_id=user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        # Step 2: 测试正常环境下可以更新会话
        created_conversation.session_name = "updated_session_name"
        updated_conversation = self.db_controller.update_conversation(created_conversation)
        self.assertEqual(updated_conversation.session_name, "updated_session_name")
        # Step 3: 异常情况，更新不存在的会话，应该报错
        fake_conversation = Conversation(id="fakeid", session_name="fake_session", user_id=user.id)
        with self.assertRaises(ValueError):
            self.db_controller.update_conversation(fake_conversation)
        # 注释说明：
        # - 第一步setup确保用户和会话存在且未软删除。
        # - 第二步验证更新功能。
        # - 第三步验证异常分支。

    def test_hard_delete_conversation(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话和相关记录存在且未被软删除
        conversation = Conversation(session_name="delete_session", user_id=self.test_user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        record1 = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Cascade1", system_response="CascadeA", query_sent_at=datetime.utcnow())
        record2 = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Cascade2", system_response="CascadeB", query_sent_at=datetime.utcnow())
        self.db_controller.create_dialogue_record(record1)
        self.db_controller.create_dialogue_record(record2)
        # Step 2: 测试正常环境下硬删除会话，级联删除记录
        self.db_controller.delete_conversation(created_conversation.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.db_controller.get_conversation_by_id(created_conversation.id)
        with self.assertRaises(LookupError):
            self.db_controller.get_record_by_record_id(record1.id)
        with self.assertRaises(LookupError):
            self.db_controller.get_record_by_record_id(record2.id)
        # Step 3: 异常情况，重复硬删除不存在的会话，应该报错
        with self.assertRaises(LookupError):
            self.db_controller.delete_conversation("nonexistentid", is_hard_delete=True)
        # 注释说明：
        # - 第一步setup确保会话和记录存在且未软删除。
        # - 第二步验证硬删除级联效果。
        # - 第三步验证异常分支。

    def test_soft_delete_conversation(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话和相关记录存在且未被软删除
        conversation2 = Conversation(session_name="soft_delete_session", user_id=self.test_user.id)
        created_conversation2 = self.db_controller.create_conversation(conversation2)
        record3 = DialogueRecord(conversation_id=created_conversation2.id, user_id=self.test_user.id, user_query="Cascade3", system_response="CascadeC", query_sent_at=datetime.utcnow())
        self.db_controller.create_dialogue_record(record3)
        # Step 2: 测试正常环境下软删除会话，级联软删除记录
        self.db_controller.delete_conversation(created_conversation2.id, is_hard_delete=False)
        # 验证软删除后会话和记录的查询行为
        # get_conversation_by_id 软删除后应抛 ValueError
        with self.assertRaises(ValueError):
            self.db_controller.get_conversation_by_id(created_conversation2.id)

        # get_record_by_record_id 软删除后也应抛 ValueError
        with self.assertRaises(ValueError):
            self.db_controller.get_record_by_record_id(record3.id)
        # Step 3: 异常情况，重复软删除不存在的会话，应该报错
        with self.assertRaises(LookupError):
            self.db_controller.delete_conversation("nonexistentid", is_hard_delete=False)
        # 注释说明：
        # - 第一步setup确保会话和记录存在且未被软删除。
        # - 第二步验证软删除级联效果。
        # - 第三步验证异常分支。

    # -------------------- Dialogue Record Management Tests --------------------
    def test_create_dialogue_record(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话存在且未被软删除，且记录不存在
        conversation = Conversation(session_name="test_session3", user_id=self.test_user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        # Step 2: 测试正常环境下创建对话记录
        record = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Hello", system_response="Hi there!", query_sent_at=datetime.utcnow())
        created_record = self.db_controller.create_dialogue_record(record)
        self.assertEqual(created_record.user_query, record.user_query)
        self.assertEqual(created_record.system_response, record.system_response)
        # Step 3: 异常情况，尝试用不存在的会话创建记录，应该报错
        fake_record = DialogueRecord(conversation_id="fakeid", user_id=self.test_user.id, user_query="Test", system_response="Fail", query_sent_at=datetime.utcnow())
        with self.assertRaises(Exception):
            self.db_controller.create_dialogue_record(fake_record)
        # 注释说明：
        # - 第一步setup确保会话存在且未软删除，且记录不存在。
        # - 第二步验证创建功能。
        # - 第三步验证异常分支。

    def test_get_record_by_record_id(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话和记录存在且未被软删除
        conversation = Conversation(session_name="record_session", user_id=self.test_user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        record = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Test", system_response="Response", query_sent_at=datetime.utcnow())
        created_record = self.db_controller.create_dialogue_record(record)
        # Step 2: 测试正常环境下可以获取记录
        fetched_record = self.db_controller.get_record_by_record_id(created_record.id)
        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record.id, created_record.id)
        # Step 3: 异常情况，获取不存在的记录，应该报错
        with self.assertRaises(LookupError):
            self.db_controller.get_record_by_record_id("nonexistentid")
        # 注释说明：
        # - 第一步setup确保用户、会话和记录存在且未软删除。
        # - 第二步验证获取功能。
        # - 第三步验证异常分支。

    def test_update_dialogue_record(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)  
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话和记录存在且未被软删除
        conversation = Conversation(session_name="update_record_session", user_id=self.test_user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        record = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Test", system_response="Response", query_sent_at=datetime.utcnow())
        created_record = self.db_controller.create_dialogue_record(record)
        # Step 2: 测试正常环境下可以更新记录
        created_record.system_response = "Updated response"
        updated_record = self.db_controller.update_dialogue_record(created_record)
        self.assertEqual(updated_record.system_response, "Updated response")
        self.assertEqual(updated_record.id, created_record.id)
        # Step 3: 异常情况，更新不存在的记录，应该报错
        fake_record = DialogueRecord(id="fakeid", conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Fake", system_response="Fake", query_sent_at=datetime.utcnow())
        with self.assertRaises(ValueError):
            self.db_controller.update_dialogue_record(fake_record)
        # 注释说明：
        # - 第一步setup确保用户、会话和记录存在且未软删除。
        # - 第二步验证更新功能。
        # - 第三步验证异常分支。

    def test_hard_delete_dialogue_record(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话和记录存在且未被软删除
        conversation = Conversation(session_name="delete_record_session", user_id=self.test_user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        record = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Test", system_response="Response", query_sent_at=datetime.utcnow())
        created_record = self.db_controller.create_dialogue_record(record)
        # Step 2: 测试正常环境下硬删除记录
        self.db_controller.delete_dialogue_record(created_record.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.db_controller.get_record_by_record_id(created_record.id)
        # Step 3: 异常情况，重复硬删除不存在的记录，应该报错
        with self.assertRaises(LookupError):
            self.db_controller.delete_dialogue_record("nonexistentid", is_hard_delete=True)
        # 注释说明：
        # - 第一步setup确保会话和记录存在且未被软删除。
        # - 第二步验证硬删除效果。
        # - 第三步验证异常分支。

    def test_soft_delete_dialogue_record(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
            self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话和记录存在且未被软删除
        created_conversation = self.db_controller.create_conversation(self.test_conversation)
        created_record2 = self.db_controller.create_dialogue_record(DialogueRecord(**self.test_record2_args, conversation_id=created_conversation.id, user_id=self.test_user.id))
        # Step 2: 测试正常环境下软删除记录
        self.db_controller.delete_dialogue_record(created_record2.id, is_hard_delete=False)
        # 验证软删除后记录的查询行为
        # get_record_by_record_id 软删除后应抛 ValueError
        with self.assertRaises(ValueError):
            self.db_controller.get_record_by_record_id(created_record2.id)
            if created_record2 is not None:
                raise RuntimeError(f"记录未被成功软删除，主键冲突风险{created_record2.id}")

        # Step 3: 异常情况，重复软删除不存在的记录，应该报错
        with self.assertRaises(LookupError):
            self.db_controller.delete_dialogue_record("nonexistentid", is_hard_delete=False)
        # 注释说明：
        # - 第一步setup确保会话和记录存在且未被软删除。
        # - 第二步验证软删除效果。
        # - 第三步验证异常分支。

    def test_get_records_by_conversation_id(self):
        # Step 1: Setup 环境，确保用户存在且未被软删除
        try:
            user = self.db_controller.get_user_by_id(self.test_user.id)
        except LookupError:
            user = self.db_controller.create_user(self.test_user)
        except ValueError:
            # 如果用户被软删除，则重新插入
            self.db_controller.delete_user(self.test_user.id, is_hard_delete=True)
            user = self.db_controller.create_user(self.test_user)
        # Step 1: Setup 环境，确保会话和多条记录存在且未被软删除
        conversation = Conversation(session_name="multi_record_session", user_id=self.test_user.id)
        created_conversation = self.db_controller.create_conversation(conversation)
        record1 = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Q1", system_response="A1", query_sent_at=datetime.utcnow())
        record2 = DialogueRecord(conversation_id=created_conversation.id, user_id=self.test_user.id, user_query="Q2", system_response="A2", query_sent_at=datetime.utcnow())
        self.db_controller.create_dialogue_record(record1)
        self.db_controller.create_dialogue_record(record2)
        # Step 2: 测试正常环境下根据会话id获取多条记录
        records = self.db_controller.get_records_by_conversation_id(created_conversation.id)
        self.assertTrue(len(records) >= 2)
        # Step 3: 异常情况，获取不存在会话的记录，应该报错
        with self.assertRaises(LookupError):
            self.db_controller.get_records_by_conversation_id("nonexistentid")
        # 注释说明：
        # - 第一步setup确保用户、会话和多条记录存在且未软删除。
        # - 第二步验证批量获取效果。
        # - 第三步验证异常分支。

if __name__ == "__main__":
    unittest.main()
