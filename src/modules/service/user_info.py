from dbController.database_controller import DatabaseController
from typing import Dict, Any, Optional
import logging
from service.utils import parse_id_card

logger = logging.getLogger(__name__)

class UserInfo:
    """
    用户信息类，用于存储和管理用户的相关信息
    从数据库加载和同步用户状态
    """
    def __init__(self, user_id: str, ticket_info: Optional[dict] = None, db_controller: Optional[DatabaseController] = None):
        """
        初始化用户信息
        
        Args:
            user_id: 用户ID
            ticket_info: 可选的火车票信息
            db_controller: 数据库控制器实例，如果不提供则创建新实例
        """
        self.user_id = user_id
        self.ticket_info = ticket_info or {}
        self._db = db_controller or DatabaseController()
        self._user_data = None
        self._load_user_data()

    def _load_user_data(self) -> None:
        """从数据库加载用户数据"""
        try:
            self._user_data = self._db.get_user_by_id(self.user_id)
            if self._user_data is None:
                logger.warning(f"用户 {self.user_id} 在数据库中不存在，将使用默认值")
                self._user_data = self._create_default_user()
        except Exception as e:
            logger.error(f"加载用户 {self.user_id} 数据失败: {e}")
            self._user_data = self._create_default_user()

    def _create_default_user(self) -> Dict[str, Any]:
        """创建默认用户数据"""
        try:
            user_data = {
                "username": f"user_{self.user_id[:8]}",
                "email": f"user_{self.user_id[:8]}@example.com",
                "is_active": True,
                "preferences": {"theme": "light", "language": "zh-CN"}
            }
            user_id = self._db.create_user(user_data)
            logger.info(f"已为 {self.user_id} 创建默认用户数据")
            return self._db.get_user_by_id(user_id) or user_data
        except Exception as e:
            logger.error(f"创建用户 {self.user_id} 默认数据失败: {e}")
            return {
                "id": self.user_id,
                "username": f"user_{self.user_id[:8]}",
                "preferences": {}
            }

    def get_preferences(self) -> Dict[str, Any]:
        """获取用户偏好设置"""
        if self._user_data:
            return self._user_data.get("preferences", {})
        return {}

    def update_preferences(self, preferences: Dict[str, Any]) -> bool:
        """更新用户偏好设置"""
        try:
            if self._db.update_user_preferences(self.user_id, preferences):
                if self._user_data:
                    self._user_data["preferences"] = preferences
                return True
            return False
        except Exception as e:
            logger.error(f"更新用户 {self.user_id} 偏好设置失败: {e}")
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        返回: 用户的相关信息字典
        """
        info = {
            "user_id": self.user_id,
            "ticket_info": self.ticket_info
        }
        if self._user_data:
            info.update({
                "username": self._user_data.get("username", ""),
                "email": self._user_data.get("email", ""),
                "preferences": self._user_data.get("preferences", {}),
                "is_active": self._user_data.get("is_active", True)
            })
        return info

    def parse_user_info(self) -> list:
        """
        解析用户ID信息
        返回: 用户ID所蕴含信息的字典列表
        """
        logger.debug(f"开始解析用户ID: {self.user_id}")
        parsed_data = parse_id_card(self.user_id)
        if not parsed_data:
            logger.warning(f"用户ID解析失败: {self.user_id}")
            return []

        logger.debug(f"解析的原始数据: {parsed_data}")

        # 构造第一个字典，包含英文性别和地点
        # 根据年龄映射为 child, teenager, adult
        age_str = parsed_data.get('age')
        age = None
        age_group = 'unknown'
        if age_str is not None:
            try:
                age = int(age_str)
                if age < 13:
                    age_group = 'child'
                elif age < 18:
                    age_group = 'teenager'
                else:
                    age_group = 'adult'
            except (ValueError, TypeError):
                age_group = 'unknown'
        
        logger.debug(f"年龄信息: age_str={age_str}, age={age}, age_group={age_group}")
        
        info1 = {
            '出生日期': parsed_data.get('birth_date'),
            '性别': parsed_data.get('gender_en'),
            '年龄': age if age is not None else age_str,
            '年龄段': age_group,
            '出生地': parsed_data.get('birth_place_en')
        }

        # 构造第二个字典，包含中文信息
        # 安全地获取province和city字段
        province = parsed_data.get('province', '')
        city = parsed_data.get('city', '')
        logger.debug(f"地址信息: province={province}, city={city}")
        
        # 构建出生地字符串，处理None值
        birth_place_parts = []
        if province:
            birth_place_parts.append(province)
        if city and city != province:  # 避免直辖市重复
            birth_place_parts.append(city)
        birth_place_str = " ".join(birth_place_parts) if birth_place_parts else "未知"
        
        info2 = {
            '出生日期': parsed_data.get('birth_date'),
            '性别': parsed_data.get('gender'),
            '年龄': age_str,
            '出生地': birth_place_str
        }

        logger.debug(f"构造的用户信息: info1={info1}, info2={info2}")
        return [info1, info2]
