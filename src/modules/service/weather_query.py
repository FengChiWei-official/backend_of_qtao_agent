
import requests, re, json
from src.modules.service.basis.tool import Tool
from src.modules.service.user_info import UserInfo
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
city_file_path = project_root / 'dataset' / 'public' / 'citycode.json'

weatherquery_desc = '''天气查询：本接口用于查询天气。接口输入格式：{\"地名\":<用户给出的地名>}'''

class WeatherQuery(Tool):
    def __init__(self, name="天气查询", description=weatherquery_desc):
        """
        初始化，读取城市数据
        :param city_file_path: 存放城市编号的JSON文件路径
        """
        super().__init__(name, description)

        self.urlWeather = "https://www.amap.com/service/weather?adcode={}"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
        }
        # 读取城市数据
        with open(city_file_path, 'r', encoding="utf-8") as f:
            self.urlCity = json.load(f)
        self.city_list = self._getCity()

    def _getCity(self):
        """
        查询所有城市和编号
        :return: 返回一个包含所有城市的列表
        """
        city = []
        if "data" in self.urlCity:
            cityByLetter = self.urlCity["data"]["cityByLetter"]
            for k, v in cityByLetter.items():
                city.extend(v)
        return city


    def __call__(self, parameter: dict, user_info: UserInfo, history: list) -> dict:
        """
        查询天气信息
        :param user_info: 用户信息
        :return: 查询的天气信息
        """
        adcode = list(filter(lambda d: d["name"] == parameter['地名'], self.city_list))[0]['adcode']

        info = {}
        response = requests.get(url=self.urlWeather.format(adcode), headers=self.headers)
        content = response.json()
        info["天气"] = content["data"]["data"][1]["forecast_data"][0]["weather_name"]
        info["最高温度"] = content["data"]["data"][1]["forecast_data"][0]["max_temp"]
        info["最低温度"] = content["data"]["data"][1]["forecast_data"][0]["min_temp"]

        return info
        # 模拟天气查询
        # return {"weather": "晴天", "temperature": "25°C"}

if __name__ == "__main__":
    # 测试天气查询
    weather_query = WeatherQuery()
    user_info = UserInfo(user_id=1, ticket_info={})
    history = []
    parameter = {"地名": "北京"}

    result = weather_query(parameter, user_info, history)
    print(result)  # 输出查询结果