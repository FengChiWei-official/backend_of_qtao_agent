import unittest
import os
import copy  # 添加深拷贝支持
from src.modules.dbController.models.user import User
from src.modules.dbController.basis.dbSession import DatabaseSessionManager as DM
from src.modules.dbController.dao.user_dao import UserDAO
from src.modules.dbController.models.conversation import Conversation
from src.modules.dbController.dao.conversation_dao import ConversationDAO
from config.loadConfig import ConfigLoader

PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

class TestUserDAO(unittest.TestCase):
    def setUp(self):
        self.config = ConfigLoader(os.path.join(PATH_TO_ROOT, "config", "config.yaml"))
        self.db_session_manager = DM(self.config.get_db_config())
        self.user_dao = UserDAO(self.config.get_db_config())
        self.test_user = User(username="testuser233", id="233333", password_hash="dummyhash", email="testuser@example.com")
        self.conflict_user = User(username="conflictuser", id="444444", password_hash="conflicthash", email="conflictuser@example.com")

        self.conversation_dao = ConversationDAO(self.config.get_db_config())  # Assuming you have a conversation DAO, initialize it here if needed
    def test_create_user(self):
        # Ensure user does not exist
        try:
            self.user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        # Create user
        created_user = self.user_dao.create_user(copy.deepcopy(self.test_user))
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.username, self.test_user.username)

        # test user already exists
        with self.assertRaises(LookupError):
            self.user_dao.create_user(copy.deepcopy(self.test_user))
        
        # test user already exists, but soft-deleted
        self.user_dao.delete_user(self.test_user.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.user_dao.create_user(copy.deepcopy(self.test_user))
        
        # test user with conflict email
        user2 = copy.deepcopy(self.test_user)
        user2.id = self.conflict_user.id
        with self.assertRaises(AttributeError):
            self.user_dao.create_user(user2)
        try:
            self.user_dao.delete_user(str(user2.id), is_hard_delete=True)  # Clean up conflict user
        except Exception:
            pass
        # if email is null
        user2 = copy.deepcopy(self.test_user)
        user2.id = self.conflict_user.id
        user2.email = None
        with self.assertRaises(AttributeError):
            self.user_dao.create_user(user2)
        

    def test_get_user_by_username(self):
        # Ensure user exists and is not soft-deleted
        try:
            self.user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.user_dao.create_user(copy.deepcopy(self.test_user))

        # Query by username
        fetched_user = self.user_dao.get_user_by_username(self.test_user.username)
        self.assertIsNotNone(fetched_user)
        self.assertEqual(fetched_user.username, self.test_user.username)

        # Query non-existent user
        with self.assertRaises(LookupError):
            self.user_dao.get_user_by_username("nonexistentuser")

        # Query soft-deleted user
        self.user_dao.delete_user(user.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.user_dao.get_user_by_username(self.test_user.username)

    def test_get_a_user_by_id(self):
        # Ensure user exists and is not soft-deleted
        try:
            self.user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.user_dao.create_user(copy.deepcopy(self.test_user))

        # Query by id
        fetched_user = self.user_dao.get_user_by_id(self.test_user.id)
        self.assertIsNotNone(fetched_user)
        self.assertEqual(fetched_user.id, self.test_user.id)
        # Query non-existent user
        with self.assertRaises(LookupError):
            self.user_dao.get_user_by_id("nonexistentid")
        # Query soft-deleted user
        self.user_dao.delete_user(user.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.user_dao.get_user_by_id(self.test_user.id)

    def test_update_user(self):
        # Ensure user exists and is not soft-deleted
        try:
            self.user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.user_dao.create_user(copy.deepcopy(self.test_user))

        # Update password
        bk_pwd = user.password_hash
        user.password_hash = "newpasswordhash"
        updated_user = self.user_dao.update_user(user)
        self.assertEqual(updated_user.password_hash, "newpasswordhash")
        # Restore password
        user.password_hash = bk_pwd
        user = self.user_dao.update_user(user)
        self.assertEqual(user.password_hash, bk_pwd)

        # Update email to conflict
        try:
            self.user_dao.create_user(copy.deepcopy(self.conflict_user))
        except Exception:
            pass
        user.email = self.conflict_user.email
        with self.assertRaises(AttributeError):
            self.user_dao.update_user(user)

        try:
            self.user_dao.delete_user(self.conflict_user.id, is_hard_delete=True)
        except LookupError:
            pass

    def test_hard_delete_user(self):
        # Ensure user exists and is not soft-deleted
        try:
            self.user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass   
        user = self.user_dao.create_user(copy.deepcopy(self.test_user))

        # Hard delete user
        self.user_dao.delete_user(user.id, is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.user_dao.get_user_by_id(user.id)
        # try to delete soft-deleted user
        user = self.user_dao.create_user(copy.deepcopy(self.test_user))
        self.user_dao.delete_user(user.id, is_hard_delete=False)
        self.user_dao.delete_user(str(user.id), is_hard_delete=True)
        with self.assertRaises(LookupError):
            self.user_dao.get_user_by_id(user.id)
        # Robustness: Try to delete again
        with self.assertRaises(LookupError):
            self.user_dao.delete_user(user.id, is_hard_delete=True)
        

    def test_soft_delete_user(self):
        # Ensure user exists and is not soft-deleted
        try:
            self.user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.user_dao.create_user(copy.deepcopy(self.test_user))
        # Soft delete user
        self.user_dao.delete_user(user.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.user_dao.get_user_by_id(user.id)
        # Robustness: Try to soft delete again
        with self.assertRaises(ValueError):
            self.user_dao.delete_user(user.id, is_hard_delete=False)  
    
    def test_check_ownership(self):
        # Ensure user exists and is not soft-deleted
        try:
            self.user_dao.delete_user(self.test_user.id, is_hard_delete=True)
        except Exception:
            pass
        user = self.user_dao.create_user(copy.deepcopy(self.test_user))
        conv = self.conversation_dao.create_conversation(
            Conversation(
                id="test_conversation",
                user_id=user.id,
                title="Test Conversation",
                is_removed=False
            )
        )


        
        # Check ownership
        self.assertTrue(self.user_dao.check_user_ownership(user.id, conv.id))
        self.assertFalse(self.user_dao.check_user_ownership(user.id, "nonexistentid"))
        
        # Soft delete user and check ownership
        self.user_dao.delete_user(user.id, is_hard_delete=False)
        with self.assertRaises(ValueError):
            self.user_dao.check_user_ownership(user.id, user.id)

if __name__ == "__main__":
    unittest.main()
