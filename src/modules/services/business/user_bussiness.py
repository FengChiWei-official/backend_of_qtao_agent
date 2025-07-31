from src.modules.dbController.dao.user_dao import UserDAO
from src.modules.dbController.models.user import User
from src.modules.services.dto.dto import UserDTO
import hashlib

def to_hash(password: str) -> str:
    """
    使用 SHA-256 哈希算法对密码进行加密
    :param password: 明文密码
    :return: 加密后的密码哈希
    """
    return hashlib.sha256(password.encode()).hexdigest()

class UserBusiness:
    def __init__(self, config: dict):
        self.user_dao = UserDAO(config)

    def register_user(self, user_id: str, username: str, email: str, password: str) -> UserDTO:
        """
        注册新用户
        :param user_id: 用户 ID
        :param username: 用户名
        :param email: 用户邮箱
        :param password: 用户密码
        :return: 注册成功的用户 DTO
        :raises ValueError: 如果用户 ID、用户名或密码为空
        :raises LookupError: 如果用户已存在
        :raises ValueError: 如果密码不符合要求
        :raises AttributeError: 如果用户信息不完整
        """
        # 参数校验
        if not user_id or not user_id.strip() or not username or not username.strip() or not password or not password.strip():
            raise ValueError("User ID, username and password are required.")
        password_hash = to_hash(password)
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
        """
        用户登录
        :param username: 用户名
        :param password: 用户密码
        :return: 登录成功的用户 DTO
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果密码不正确
        """
        try:
            user = self.user_dao.get_user_by_username(username)
        except (LookupError, ValueError) as e:
            raise LookupError(f"dao error, {username} not found") from e
        password_hash = to_hash(password)
        if user.password_hash != password_hash:
            raise ValueError("Incorrect password.")
        return UserDTO.from_obj(user)

    def get_user_info(self, user_id: str) -> UserDTO:
        """
        获取用户信息    
        :param user_id: 用户 ID
        :return: 用户 DTO
        :raises LookupError: 如果用户不存在
        """
        try:
            user = self.user_dao.get_user_by_id(user_id)
        except (LookupError, ValueError) as e:
            raise LookupError(f"dao error, {user_id} not found") from e
        user = self.user_dao.get_user_by_id(user_id)
        return UserDTO.from_obj(user)

    def update_user_email(self, user_id: str, new_email: str) -> UserDTO:
        """
        更新用户邮箱
        :param user_id: 用户 ID
        :param new_email: 新邮箱地址
        :return: 更新后的用户 DTO
        :raises LookupError: 如果用户不存在
        :raises ValueError: 如果新邮箱格式不正确
        :raises AttributeError: 如果新邮箱已被其他用户使用
        """
        if not new_email or "@" not in new_email:
            raise ValueError("Invalid email format.")
        try:
            user = self.user_dao.get_user_by_id(user_id)
        except (LookupError, ValueError) as e:
            raise LookupError(f"dao error, {user_id} not found") from e
        user.email = new_email
        try:
            user = self.user_dao.update_user(user)
        except (LookupError, ValueError) as e:
            raise LookupError(f"dao error, noway! {user_id} not found") from e
        except AttributeError as e:
            raise AttributeError(f"dao error, email conflict with others") from e
        return UserDTO.from_obj(user)

    def delete_user(self, user_id: str, is_hard_delete: bool = False) -> None:
        """
        删除用户
        :param user_id: 用户 ID
        :param is_hard_delete: 是否进行硬删除
        :raises LookupError: 如果用户不存在
        
        """
        self.user_dao.delete_user(user_id, is_hard_delete)


    def check_conversation_ownership(self, user_id: str, conversation_id: str) -> bool:
        """
        检查用户是否拥有指定会话
        :param user_id: 用户 ID
        :param conversation_id: 会话 ID
        :return: 如果用户拥有该会话则返回 True，否则返回 False
        """
        return self.user_dao.check_user_ownership(user_id, conversation_id)