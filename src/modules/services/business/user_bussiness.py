from src.modules.dbController.dao.user_dao import UserDAO
from src.modules.dbController.models.user import User
from src.modules.services.dto.dto import UserDTO
import hashlib

class UserBusiness:
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao

    def register_user(self, user_id: str, username: str, email: str, password: str) -> UserDTO:
        # 参数校验
        if not user_id or not user_id.strip() or not username or not username.strip() or not password or not password.strip():
            raise ValueError("User ID, username and password are required.")
        # 密码加密（简单示例，建议用更安全的hash算法）
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=True
        )
        try:
            user = self.user_dao.create_user(user)
        except (LookupError, ValueError, AttributeError) as e:
            raise e
        return UserDTO.from_obj(user)

    def login_user(self, username: str, password: str) -> UserDTO:
        user = self.user_dao.get_user_by_username(username)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash != password_hash:
            raise ValueError("Incorrect password.")
        return UserDTO.from_obj(user)

    def get_user_info(self, user_id: str) -> UserDTO:
        user = self.user_dao.get_user_by_id(user_id)
        return UserDTO.from_obj(user)

    def update_user_email(self, user_id: str, new_email: str) -> UserDTO:
        user = self.user_dao.get_user_by_id(user_id)
        user.email = new_email
        user = self.user_dao.update_user(user)
        return UserDTO.from_obj(user)

    def delete_user(self, user_id: str, is_hard_delete: bool = False) -> None:
        self.user_dao.delete_user(user_id, is_hard_delete)
