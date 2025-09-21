import os, sys
import numpy as np
import Levenshtein
from src.utils.root_path import get_root_path
if str(get_root_path()) not in sys.path:
    sys.path.append(str(get_root_path()))
PATH_TO_ROOT = get_root_path()
import requests, re, json
from src.modules.services.service_basis.basis.tool import Tool
from src.modules.services.service_basis.user_info import UserInfo

city_file_path = PATH_TO_ROOT / 'dataset' / 'public' / 'citycode.json'

weatherquery_desc = '''天气查询：本接口用于查询天气。接口输入格式：{"城市名":<用户想要查询的城市名>, "日期":<用户希望查询的日期>}，其中<日期>格式应该形如："2025-06-07"（月和日均为两位数）'''

class WeatherQuery(Tool):
    def __init__(self, name="天气查询", description=weatherquery_desc):
        super().__init__(name, description)

        self.url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.key = "0239a191dae57fa5074ddf229bd93510" # os.environ.get('amapKey', '')

        with open(city_file_path, 'r', encoding="utf-8") as f:
            self.urlCity = json.load(f)
        self.city_list = self._getCity()
        self.city_names = [city['name'] for city in self.city_list]

    def _getCity(self):
        city = []
        if "data" in self.urlCity:
            cityByLetter = self.urlCity["data"]["cityByLetter"]
            for k, v in cityByLetter.items():
                city.extend(v)
        return city

    def normalized_similarity(self, city1:str, city2: str):
        distance = Levenshtein.distance(city1, city2)
        max_len = max(len(city1), len(city2))
        if max_len == 0:
            return 1.0
        return 1 - (distance / max_len)

    def fuzzy_search(self, query_city: str):
        scores = []
        for city_name in self.city_names:
            score = self.normalized_similarity(query_city, city_name)
            scores.append(score)
        sorted_idx = np.array(scores).argsort().tolist()[::-1]
        return [self.city_names[idx] for idx in sorted_idx[:5]]


    def __call__(self, parameter: dict, user_info: UserInfo, history: list) -> dict:
        info = {}

        adcode = list(filter(lambda d: d["name"] == parameter['城市名'], self.city_list))
        if len(adcode) == 0:
            info["错误"] = f"查询失败，{parameter['城市名']}不是一个合法的城市名！你可能想查询的是：{'、'.join(self.fuzzy_search(parameter['城市名']))}。"
        else:
            adcode = adcode[0]['adcode']
            
            # 构建API请求URL
            url = f"{self.url}?key={self.key}&city={adcode}&extensions=all"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                if data['status'] == '1' and 'forecasts' in data:
                    forecasts = data['forecasts'][0]['casts']
                    
                    # 获取请求的日期，如果没有指定日期则返回今天的天气
                    target_date = parameter.get('日期', None)
                    
                    if target_date:
                        # 查找指定日期的天气
                        for forecast in forecasts:
                            if forecast['date'] == target_date:
                                info["日期"] = forecast['date']
                                info["星期"] = forecast['week']
                                info["白天天气"] = forecast['dayweather']
                                info["夜间天气"] = forecast['nightweather']
                                info["白天温度"] = forecast['daytemp'] + "°C"
                                info["夜间温度"] = forecast['nighttemp'] + "°C"
                                info["白天风向"] = forecast['daywind']
                                info["夜间风向"] = forecast['nightwind']
                                info["白天风力"] = forecast['daypower']
                                info["夜间风力"] = forecast['nightpower']
                                break
                        else:
                            info["错误"] = f"未找到{target_date}的天气预报数据"
                    else:
                        # 返回今天的天气
                        if forecasts:
                            forecast = forecasts[0]
                            info["日期"] = forecast['date']
                            info["星期"] = forecast['week']
                            info["白天天气"] = forecast['dayweather']
                            info["夜间天气"] = forecast['nightweather']
                            info["白天温度"] = forecast['daytemp'] + "°C"
                            info["夜间温度"] = forecast['nighttemp'] + "°C"
                            info["白天风向"] = forecast['daywind']
                            info["夜间风向"] = forecast['nightwind']
                            info["白天风力"] = forecast['daypower']
                            info["夜间风力"] = forecast['nightpower']
                else:
                    info["错误"] = f"获取{parameter['城市名']}天气信息失败"
                    
            except Exception as e:
                info["错误"] = f"天气查询服务异常：{str(e)}"

        return info

if __name__ == "__main__":
    # 测试天气查询
    weather_query = WeatherQuery()
    user_info = UserInfo(user_id="1", ticket_info={})
    history = []
    
    # 测试查询北京今天的天气
    parameter1 = {"城市名": "北京"}
    result1 = weather_query(parameter1, user_info, history)
    print("今天北京天气:", result1)
    
    # 测试查询上海指定日期的天气
    parameter2 = {"城市名": "上海", "日期": "2025-09-21"}
    result2 = weather_query(parameter2, user_info, history)
    print("2025-09-21上海天气:", result2)