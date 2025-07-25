from src.utils.root_path import get_root_path

PATH_TO_ROOT = get_root_path()

json_path = PATH_TO_ROOT / 'dataset' / 'public' / 'citycode.json'

def format_ticket_info(ticket_info: dict) -> str:
    """
    格式化票务信息
    :param ticket_info: 票务信息字典
    :return: 格式化后的票务信息字符串
    """
    return f"票务状态: {ticket_info['ticket_status']}, 票价: {ticket_info['ticket_price']}"

import json
from datetime import datetime
from pathlib import Path
from enum import Enum

# 全局变量，缓存城市代码数据
city_code_data = None

class Act(Enum):
    CHAT = 0
    RESTAURANT_RECOMMEND = 1
    CUISINE_RECOMMEND = 2
    TRAIN_QUERY = 3
    WEATHER_QUERY = 4
    
def get_city_code_map():
    """加载并缓存城市代码数据"""
    global city_code_data
    if city_code_data is None:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                city_code_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading citycode.json: {e}")
            raise
    return city_code_data

def get_address_from_code(code: str) -> dict:
    """根据6位地址码获取地址中英文"""
    city_data = get_city_code_map()
    if not city_data:
        return {
            "cn": "未知", 
            "en": "Unknown",
            "province": "",
            "city": ""
        }

    provinces = city_data.get('data', {}).get('cityData', {}).get('provinces', {})
    
    province_code = code[:2] + '0000'
    city_code = code[:4] + '00'
    
    province_info = provinces.get(province_code)
    if not province_info:
        return {
            "cn": "未知", 
            "en": "Unknown",
            "province": "",
            "city": ""
        }
        
    province_name_cn = province_info.get('name', '')
    province_name_en = province_info.get('name_en', '')

    # 查找市
    city_name_cn = ''
    city_name_en = ''
    if province_name_cn:
        cities = province_info.get('cities', [])
        for city in cities:
            if city.get('adcode') == city_code:
                city_name_cn = city.get('name', '')
                city_name_en = city.get('name_en', '')
                break
    
    # 对于直辖市
    if not city_name_cn and province_name_cn in ["北京", "天津", "上海", "重庆"]:
        city_name_cn = province_name_cn
        city_name_en = province_name_en

    cn_parts = []
    if province_name_cn and province_name_cn != city_name_cn:
        cn_parts.append(province_name_cn)
    if city_name_cn:
        cn_parts.append(city_name_cn)
    
    en_parts = []
    if city_name_en:
        en_parts.append(city_name_en)
    if province_name_en and province_name_en != city_name_en:
        en_parts.append(province_name_en)
        
    return {
        "cn": " ".join(cn_parts) or "未知",
        "en": ", ".join(en_parts) or "Unknown",
        "province": province_name_cn,
        "city": city_name_cn
    }

def parse_id_card(id_card_number: str) -> dict:
    """
    解析18位中国身份证号码
    """
    if not isinstance(id_card_number, str) or len(id_card_number) != 18:
        return {}

    try:
        address_code = id_card_number[:6]
        birth_date_str = id_card_number[6:14]
        gender_digit = int(id_card_number[16])

        birth_date = datetime.strptime(birth_date_str, '%Y%m%d')
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        gender = '男' if gender_digit % 2 != 0 else '女'
        gender_en = 'male' if gender == '男' else 'female'
        
        birth_place_info = get_address_from_code(address_code)

        return {
            'birth_date': birth_date.strftime('%Y/%m/%d'),
            'age': str(age),
            'gender': gender,
            'gender_en': gender_en,
            'birth_place': birth_place_info['cn'],
            'birth_place_en': birth_place_info['en'],
            'province': birth_place_info['province'],
            'city': birth_place_info['city']
        }
    except (ValueError, TypeError):
        return {}
