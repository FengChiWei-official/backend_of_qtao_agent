# -*- coding: utf-8 -*-
"""
预处理工具模块，包含各种数据预处理工具函数
"""

from datetime import datetime

# 中文省份名称映射字典
PROVINCE_MAPPING = {
    'Beijing': '北京',
    'Tianjin': '天津',
    'Hebei': '河北',
    'Shanxi': '山西',
    'Nei Mongol': '内蒙古',
    'Liaoning': '辽宁',
    'Jilin': '吉林',
    'Heilongjiang': '黑龙江',
    'Shanghai': '上海',
    'Jiangsu': '江苏',
    'Zhejiang': '浙江',
    'Anhui': '安徽',
    'Fujian': '福建',
    'Jiangxi': '江西',
    'Shandong': '山东',
    'Henan': '河南',
    'Hubei': '湖北',
    'Hunan': '湖南',
    'Guangdong': '广东',
    'Guangxi': '广西',
    'Hainan': '海南',
    'Chongqing': '重庆',
    'Sichuan': '四川',
    'Guizhou': '贵州',
    'Yunnan': '云南',
    'Xizang': '西藏',
    'Shanxi2': '陕西',
    'Gansu': '甘肃',
    'Qinghai': '青海',
    'Ningxia': '宁夏',
    'Xinjiang': '新疆'
}

def calculate_age(birthdate):
    """
    计算年龄
    
    Args:
        birthdate (str): 格式为 yyyy/mm/dd 的出生日期
        
    Returns:
        int: 年龄
    """
    # 假设出生日期格式为 yyyy/mm/dd
    birth_date = datetime.strptime(birthdate, "%Y/%m/%d")
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def map_to_age_group(age):
    """
    将年龄映射到年龄段
    
    Args:
        age (int): 年龄
        
    Returns:
        str: 年龄段 ('child', 'teenager', 'adult', 'middle-ager', 'elderly')
    """
    if 0 <= age <= 5:
        return 'child'
    elif 6 <= age <= 17:
        return 'teenager'
    elif 18 <= age <= 34:
        return 'adult'
    elif 35 <= age <= 49:
        return 'middle-ager'
    elif age >= 50:
        return 'elderly'
    return None

def extract_province(birthplace):
    """
    从出生地提取省份信息
    
    Args:
        birthplace (str): 出生地字符串，格式为 "省份 城市"
        
    Returns:
        str: 提取的省份名称
    """
    if not birthplace or pd.isna(birthplace):
        return None
    
    # 假设出生地格式为 "省份 城市"
    parts = birthplace.split()
    if len(parts) > 0:
        return parts[0]
    return None

# 在模块导入时避免循环依赖
import pandas as pd