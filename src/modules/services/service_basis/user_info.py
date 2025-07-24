import os, sys

from .utils import PATH_TO_ROOT
if str(PATH_TO_ROOT) not in sys.path:
    sys.path.append(str(PATH_TO_ROOT))

DATASET_ITEM_PATH = PATH_TO_ROOT / 'dataset' / 'meal_service' / 'item.csv'
from typing import Optional
import logging
from .utils import parse_id_card

logger = logging.getLogger(__name__)

class UserInfo:
    """
    用户信息类，用于存储和管理用户的相关信息
    从数据库加载和同步用户状态
    """
    def __init__(self, user_id: str, ticket_info: Optional[dict] = None):
        """
        初始化用户信息
        
        Args:
            user_id: 用户ID
            ticket_info: 可选的火车票信息
            db_controller: 数据库控制器实例，如果不提供则创建新实例
        """
        self.user_id = user_id
        self.ticket_info = ticket_info or {}
        self._user_data = self.parse_user_info()[0]

    def __repr__(self):
        return f"UserInfo(user_id={self.user_id}, ticket_info={self.ticket_info}, user_data={self._user_data})"
    def __str__(self):
        return self.__repr__()
    
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
