import unittest
from unittest.mock import patch, MagicMock
from src.modules.service.weather_query import WeatherQuery
from src.modules.service.user_info import UserInfo
import json
from pathlib import Path

class TestWeatherQuery(unittest.TestCase):
    @patch('src.modules.service.weather_query.open')
    @patch('src.modules.service.weather_query.json.load')
    def setUp(self, mock_json_load, mock_open):
        # mock city data
        mock_json_load.return_value = {
            "data": {
                "cityByLetter": {
                    "B": [
                        {"name": "北京", "adcode": "110000"}
                    ]
                }
            }
        }
        self.weather_query = WeatherQuery()
        self.user_info = UserInfo(user_id=1, ticket_info={})
        self.history = []

    @patch('src.modules.service.weather_query.requests.get')
    def test_query_weather_success(self, mock_get):
        # mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "data": [
                    {},
                    {
                        "forecast_data": [
                            {
                                "weather_name": "晴",
                                "max_temp": "35",
                                "min_temp": "25"
                            }
                        ]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        param = {"地名": "北京"}
        result = self.weather_query(param, self.user_info, self.history)
        self.assertEqual(result["天气"], "晴")
        self.assertEqual(result["最高温度"], "35")
        self.assertEqual(result["最低温度"], "25")

    def test_city_not_found(self):
        param = {"地名": "不存在城市"}
        with self.assertRaises(IndexError):
            self.weather_query(param, self.user_info, self.history)

class TestWeatherQueryIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 创建真实 citycode.json 文件
        project_root = Path(__file__).resolve().parent.parent.parent
        cls.city_file_path = project_root / 'dataset' / 'citycode.json'
        cls.city_file_path.parent.mkdir(parents=True, exist_ok=True)
        city_data = {
            "data": {
                "cityByLetter": {
                    "B": [
                        {"name": "北京", "adcode": "110000"}
                    ],
                    "S": [
                        {"name": "上海", "adcode": "310000"}
                    ]
                }
            }
        }
        with open(cls.city_file_path, 'w', encoding='utf-8') as f:
            json.dump(city_data, f, ensure_ascii=False)

    @classmethod
    def tearDownClass(cls):
        # 删除 citycode.json 文件
        if cls.city_file_path.exists():
            cls.city_file_path.unlink()

    def setUp(self):
        self.weather_query = WeatherQuery()
        self.user_info = UserInfo(user_id="1", ticket_info={})
        self.history = []

    def test_get_city_list(self):
        # 测试城市列表是否包含北京和上海
        city_names = [c['name'] for c in self.weather_query.city_list]
        self.assertIn("北京", city_names)
        self.assertIn("上海", city_names)

    def test_adcode_lookup(self):
        # 测试能否正确查找城市编码
        param = {"地名": "上海"}
        adcode = list(filter(lambda d: d["name"] == param['地名'], self.weather_query.city_list))[0]['adcode']
        self.assertEqual(adcode, "310000")

    def test_city_not_found_real(self):
        # 测试真实数据下城市不存在时抛出异常
        param = {"地名": "不存在城市"}
        with self.assertRaises(IndexError):
            _ = list(filter(lambda d: d["name"] == param['地名'], self.weather_query.city_list))[0]['adcode']

if __name__ == "__main__":
    unittest.main()
