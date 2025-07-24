import unittest
import json
import os
from pathlib import Path
from src.modules.service_basis import utils

class TestUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 创建依赖的 citycode.json 文件
        cls.json_path = utils.json_path
        cls.json_path.parent.mkdir(parents=True, exist_ok=True)
        city_data = {
            "data": {
                "cityData": {
                    "provinces": {
                        "110000": {
                            "name": "北京",
                            "name_en": "Beijing",
                            "cities": [
                                {"adcode": "110100", "name": "北京市", "name_en": "Beijing City"}
                            ]
                        }
                    }
                }
            }
        }
        with open(cls.json_path, 'w', encoding='utf-8') as f:
            json.dump(city_data, f, ensure_ascii=False)

    @classmethod
    def tearDownClass(cls):
        if cls.json_path.exists():
            cls.json_path.unlink()

    def test_format_ticket_info(self):
        info = {'ticket_status': '已出票', 'ticket_price': '100'}
        result = utils.format_ticket_info(info)
        self.assertIn('票务状态: 已出票', result)
        self.assertIn('票价: 100', result)

    def test_get_address_from_code(self):
        code = '110100'  # 北京市
        result = utils.get_address_from_code(code)
        self.assertEqual(result['province'], '北京')
        self.assertEqual(result['city'], '北京市')
        self.assertIn('北京', result['cn'])
        self.assertIn('Beijing', result['en'])

    def test_get_address_from_code_unknown(self):
        code = '999999'
        result = utils.get_address_from_code(code)
        self.assertEqual(result['cn'], '未知')
        self.assertEqual(result['en'], 'Unknown')

    def test_parse_id_card(self):
        # 身份证号: 北京市 1990-01-01 男
        id_card = '110100199001011234'
        result = utils.parse_id_card(id_card)
        self.assertEqual(result['gender'], '男')
        self.assertEqual(result['gender_en'], 'male')
        self.assertEqual(result['birth_place'], '北京 北京市')
        self.assertEqual(result['province'], '北京')
        self.assertEqual(result['city'], '北京市')
        self.assertEqual(result['birth_date'], '1990/01/01')
        self.assertTrue(result['age'].isdigit())

    def test_parse_id_card_invalid(self):
        id_card = '1234567890'
        result = utils.parse_id_card(id_card)
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
