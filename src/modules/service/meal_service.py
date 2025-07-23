import pandas as pd
from openai import OpenAI
import re, json
import numpy as np
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.modules.service.utils import Tool
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein
import time
from typing import Iterable



# 路径常量集中管理
import os
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
DATASET_ITEM_PATH = os.path.join(PATH_TO_ROOT, 'dataset', 'meal_service', 'item.csv')



recommend_prompt = \
'''
【任务】 基于用户信息和历史对话，推荐用户最有可能想要的{top_k}个餐食
【格式要求】 先进行思考和分析，然后按Python列表格式输出推荐结果：["<推荐餐食名1>", "<推荐餐食名2>", ..., "<推荐餐食名{top_k}>"]
【用户信息】 {user_info}
【历史对话】 {dialogue}
'''

# 怎样才算“同一样”食物
judge_prompt = \
'''
【任务】 为候选集中的每一个餐食在检索结果中寻找相匹配的餐食，这里“相匹配”指二者是同一样食物
【输出格式】 
先进行思考和分析，然后输出一个字典，字典的键是候选集中每一个餐食的名字，对应的值是在检索结果中与之相匹配的一个食品的字典：{{"<候选餐食1>": "<匹配餐食1>", ..., "<候选餐食n>":"<匹配餐食n>"}}
如果不存在相匹配的餐食，则对应的值为None；
如果有多个相匹配的餐食，则选择匹配程度最高的哪一个。
【候选集】 {raw_candidates}
【检索结果】 {retrieved_items}
'''

encoding_prompt = \
'''
【任务】 
判断给定餐食的特征。
你要判断的特征有：
饮食类型：(1)正餐、(2)小吃、(3)饮料/咖啡、(0)未加限定
菜系：(1)川菜、(2)粤菜、(3)鲁菜、(4)淮扬菜、(5)闽菜、(6)湘菜、(7)西北菜、(8)东北菜、(0)未加限定
中西餐：(1)中餐、(2)西餐、(3)素食、(4)清真、(0)未加限定
辣度：4个1/0，分别表示是否不辣、是否微辣、是否中辣、是否特辣（其中1表示是，0表示不是）
价格：包含两个整数的列表[a, b]或"未加限定"（其中a、b为两个非负整数，且满足a<=b）
北京/天津/河北/山西/内蒙古/辽宁/吉林/黑龙江/上海/江苏/浙江/安徽/福建/江西/山东/河南/湖北/湖南/广东/广西/海南/重庆/四川/广州/云南/西藏/陕西/甘肃/青海/宁夏/新疆：该餐食对不同省份人群的适合程度，每个值的范围为1~5，1表示最不推荐，5表示最推荐
儿童/青年/成年人/中年人/老年人：该餐食对不同年龄人群的适合程度，每个值的范围为1~5，1表示最不推荐，5表示最推荐
早餐/午餐/晚餐/下午茶/夜宵：该餐食对不同时段的适合程度，每个值的范围为1~5，1表示最不推荐，5表示最推荐
男/女：该餐食对不同性别，每个值的范围为1~5，1表示最不推荐，5表示最推荐
春/夏/秋/冬：该餐食对不同季节的适合程度，每个值的范围为1~5，1表示最不推荐，5表示最推荐
【格式】 
输出要求：输出一个json，键为特征名，值为特征值。注意，饮食类型是1个特征，菜系是1个特征，中西餐是1个特征，辣度有4个特征，省份相关的有31个特征，年龄相关的有5个特征，时段相关的有5个特征，性别相关的有2个特征，季节相关的有4个特征，共52个特征值
输出示例：
```json
{{
  "饮食类型": <餐食类型>,
  "菜系": <餐食类型>,
  "中西餐": <餐食类型>,
  "不辣": <是否不辣>,
  "微辣": <是否微辣>,
  "中辣": <是否中辣>,
  "特辣": <是否特辣>,
  "价格": [<价格下限>, <价格上限>] || "未加限定" # 注意这里是一个列表，包含两个整数，或者是一个常量字符串：“未加限定”,
  "北京": <适合北京人的程度>,
  "天津": <适合天津人的程度>,
  ...,
  "新疆": <适合新疆人的程度>,
  "儿童": <适合儿童的程度>,
  "青年": <适合青年的程度>,
  "成年人": <适合成年人的程度>,
  "中年人": <适合中年人的程度>,
  "老年人": <适合老年人的程度>,
  "早餐": <适合作为早餐的程度>,
  "午餐": <适合作为午餐的程度>,
  "晚餐": <适合作为晚餐的程度>,
  "下午茶": <适合作为下午茶的程度>,
  "夜宵": <适合作为夜宵的程度>,
  "男": <适合男生的程度>,
  "女": <适合女生的程度>,
  "春": <适合春季的程度>,
  "夏": <适合夏季的程度>,
  "秋": <适合秋季的程度>,
  "冬": <适合冬季的程度>
  
}}
```
【待判断的餐食】
{items}
'''

mealservice_desc = '''订餐服务：本接口用于从数据库中匹配最符合用户偏好与要求的餐厅或菜品。接口输入格式：该接口无需输入参数，填None'''

soft_constraints = ["Beijing", "Tianjin", "Hebei", "Shanxi", "Nei Mongol", "Liaoning", "Jilin", "Heilongjiang", "Shanghai", "Jiangsu", "Zhejiang", "Anhui", "Fujian", "Jiangxi", "Shandong", "Henan", "Hubei", "Hunan", "Guangdong", "Guangxi", "Hainan", "Chongqing", "Sichuan", "Guizhou", "Yunnan", "Xizang", "Shanxi2", "Gansu", "Qinghai", "Ningxia", "Xinjiang", "child", "teenager", "adult", "middle-ager", "elderly", "breakfast", "lunch", "dinner", "afternoon-tea", "night-snack", "male", "female", "spring", "summer", "autumn", "winter"]



class MealService(Tool):
    """
    订餐服务模块，负责获取订餐信息
    """

    def __init__(self, name="订餐服务", description=mealservice_desc, topK=10):
        super().__init__(name, description)
        self.items = pd.read_csv(DATASET_ITEM_PATH)
        self.items.set_index(inplace=True, keys=['is_dinner', 'cuisine', 'food_type'])
        self.items['id'] = self.items['city_id'].astype(str) + '_' + self.items['restaurant_id'].astype(str) + '_' + self.items['food_id'].astype(str)
        self.cols = ['is_dinner', 'cuisine', 'food_type']
        self.topK = topK
        self.item_names = self.items['food_name'].to_list()

    def __call__(self, parameter: dict, user_info: dict, history: list):
        raw_candidates = self.recommend(user_info, history) #raw_candidates: ['酸辣莲藕', '酸辣土豆丝']
        print(f'候选物品集为：{raw_candidates}')

        retrieved_items = self.retrieve(raw_candidates) #retrieved_items ['土豆丝', '酸辣土豆丝', '炝土豆丝', '西红柿炒鸡蛋', '凉拌紫甘蓝']
        print(f'检索结果为：{retrieved_items}')

        judge_result = self.judge(raw_candidates, retrieved_items) #judge_result {'酸辣莲藕': None}
        print(f'连接结果为：{judge_result}')

        recommended_list = []
        for raw_candidate, linked_item in judge_result.items():
            if linked_item is not None:
                recommended_list.append(linked_item)
            else:   # To-Improve：可以同时为多个物品编码
                unmatched_item = self.encode(raw_candidate) #{'饮食类型': 2, '菜系': 0, '中西餐': 1, '不辣': 0, '微辣': 1, '中辣': 1, '特辣': 1, '价格': [5, 15], '北京': 4, '天津': 4, '河北': 4, '山西': 3, '内蒙古': 3, '辽宁': 3, '吉林': 3, '黑龙江': 3, '上海': 4, '江苏': 4, '浙江': 4, '安徽': 4, '福建': 4, '江西': 4, '山东': 3, '河南': 4, '湖北': 4, '湖南': 4, '广东': 4, '广西': 4, '海南': 3, '重庆': 4, '四川': 4, '广州': 4, '云南': 4, '西藏': 3, '陕西': 3, '甘肃': 3, '青海': 3, '宁夏': 3, '新疆': 3, '儿童': 3, '青年': 4, '成年人': 4, '中年人': 4, '老年人': 3, '早餐': 2, '午餐': 4, '晚餐': 4, '下午茶': 3, '夜宵': 2, '男': 4, '女': 4, '春': 4, '夏': 4, '秋': 4, '冬': 3}# self.encode(raw_candidate)
                match = self.KNN(unmatched_item)
                recommended_list.append({'food_id':match['id'], 'food_name':match['food_name']})
        print(f'最终推荐列表为：{recommended_list}')
        return recommended_list

    def recommend(self, user_info: dict, history: list):
        # 使用大模型进行零样本对话式推荐
        prompt = recommend_prompt.format(top_k=3, user_info=user_info, dialogue=history[:-1])
        completion_generator = self.feed_LLM(prompt)
        completion = ''
        for chunk in completion_generator:
            completion += chunk.choices[0].delta.content
        match = re.search(r'\s*(\[.*\])\s*', completion, re.DOTALL)
        raw_candidates = eval(match.group(1))
        return raw_candidates

    def retrieve(self, raw_candidates: list):
        retrieved_items = []
        for raw_candidate in raw_candidates:
            sim = []
            for item_name in self.item_names:
                sim.append(Levenshtein.distance(raw_candidate, item_name))
            top3_idx = np.array(sim).argsort().tolist() # To-Improve：可以匹配多个，再交给LLM判断
            for idx in top3_idx[:5]:
                retrieved_items.append({'food_id': self.items.iloc[idx]['id'],'food_name':self.item_names[idx]})
        df = pd.DataFrame(retrieved_items)
        # print(df)
        df = df.drop_duplicates(subset='food_name')
        retrieved_items = df.to_dict(orient='records')

        return retrieved_items

    def judge(self, raw_candidates: list, retrieved_items: list):
        # 将LLM生成的原始候选物品与实际存在物品进行链接
        prompt = judge_prompt.format(raw_candidates=raw_candidates, retrieved_items=[item['food_name'] for item in retrieved_items])
        completion_generator = self.feed_LLM(prompt)
        completion = ''
        for chunk in completion_generator:
            completion += chunk.choices[0].delta.content
        match = re.search(r'\s*(\{.*\})\s*', completion, re.DOTALL)
        judge_result = eval(match.group(1))
        for key, val in judge_result.items():
            if val is not None:
                for item in retrieved_items:
                    if item['food_name'] == val:
                        judge_result[key] = item
                        break
        return judge_result

    def encode(self, raw_candidates: list):
        prompt = encoding_prompt.format(items=raw_candidates)
        completion = self.feed_LLM(prompt)
        result = ''
        for chunk in completion:
            #print(chunk.choices[0].delta.content)
            result += chunk.choices[0].delta.content
        print(result)
        match = re.search(r'```json\s*(\{.*\})\s*```', result, re.DOTALL)
        if match:
            query = json.loads(match.group(1))
            return query
        else:
            raise ValueError("No JSON block found in LLM response.")

    # 示例: encode [烤鸭] -> {...}
    """result
    {
      "饮食类型": 1,
      "菜系": 0,
      "中西餐": 1,
      "不辣": 1,
      "微辣": 0,
      "中辣": 0,
      "特辣": 0,
      "价格": [100, 500],
      "北京": 5,
      "天津": 4,
      "河北": 4,
      "山西": 4,
      "内蒙古": 4,
      "辽宁": 4,
      "吉林": 4,
      "黑龙江": 4,
      "上海": 4,
      "江苏": 4,
      "浙江": 4,
      "安徽": 4,
      "福建": 4,
      "江西": 4,
      "山东": 4,
      "河南": 4,
      "湖北": 4,
      "湖南": 4,
      "广东": 4,
      "广西": 4,
      "海南": 4,
      "重庆": 4,
      "四川": 4,
      "广州": 4,
      "云南": 4,
      "西藏": 4,
      "陕西": 4,
      "甘肃": 4,
      "青海": 4,
      "宁夏": 4,
      "新疆": 4,
      "儿童": 3,
      "青年": 5,
      "成年人": 5,
      "中年人": 5,
      "老年人": 3,
      "早餐": 2,
      "午餐": 3,
      "晚餐": 5,
      "下午茶": 2,
      "夜宵": 2,
      "男": 5,
      "女": 5,
      "春": 4,
      "夏": 4,
      "秋": 4,
      "冬": 4
    }
    """

    def KNN(self, query: dict) -> pd.Series:
        for attr in ['饮食类型', '菜系', '中西餐']:
            if query[attr] == 0:
                query[attr] = slice(None)
        price_range = query.get('价格', '未加限定')
        if price_range != '未加限定' and isinstance(price_range, list) and len(price_range) == 2:
            filtered_items = self.items[
                (self.items['price'] >= query['价格'][0]) & (self.items['price'] <= query['价格'][1])]
        else:
            filtered_items = self.items
        print("Filtered items shape:", filtered_items.shape)
        #print(filtered_items)
        indexes = (query['饮食类型'], query['菜系'], query['中西餐'])
        filtered_items = filtered_items[(filtered_items['not-spicy']==query['不辣'])| # To-Improve：怎么编码和匹配辣度更合适？（0, 1, 0, 0匹配出凉粉）
                                        (filtered_items['slightly-spicy']==query['微辣'])|
                                        (filtered_items['medium-spicy']==query['中辣'])|
                                        (filtered_items['extra-spicy']==query['特辣'])]
        filtered_items = filtered_items.loc[indexes]
        # print(filtered_items.shape)
        # print(filtered_items)
        # vectors = filtered_items[soft_constraints].to_numpy()
        vectors = filtered_items[soft_constraints].fillna(0).to_numpy()
        # vector = np.array([query[k] for k in soft_constraints]).reshape(1, -1)
        vector = np.array(list(query.values())[8:]).reshape(1,-1)
        sim = cosine_similarity(vector, vectors)
        top_idx = sim.argmax(axis=1)
        # print(filtered_items)
        # 输出样例：
        # city_id                   17
        # restaurant_id              9
        # food_id                    7
        # food_name             野生菌炖土鸡
        # price                  298.0
        # ...（省略其它字段）...
        # id                    17_9_7
        # Name: (1.0, 1.0, 1.0), dtype: object
        return filtered_items.iloc[top_idx.item()]

    def feed_LLM(self, prompt: str) -> Iterable:
        """
        根据提示词生成回复
        :param prompt: 输入大模型的提示词
        :return: 返回一个生成器对象，迭代获取每个流式响应块（chunk），每个chunk为OpenAI API的响应对象
        """
        client = OpenAI(
            api_key="sk-8f86f5e9b0b34e8a9e7319e68f99787e",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        messages = [{'role': 'user', 'content': prompt}]
        completion = client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            stop="Observation",
            stream=True,
            stream_options={"include_usage": False}
        )
        return completion


if __name__ == "__main__":
    meal_service = MealService()

    user_info = {"出生地":"上海", "性别":"男", "年龄":"19", "当前日期": "2025-5-11"}
    history = [{'role':'user', 'content':'我想吃点脆脆的蔬菜，酸辣口味的，你有什么推荐的吗？'}, {'role':'assistant', 'content':'Thought:'}]

    start = time.time()
    meal_service({}, user_info, history)
    end = time.time()
    print(f'耗时：{end-start}')


'''    def encode(self, parameter: dict, user_info: dict, history: list) -> str:
        prompt = encoding_prompt.format(user_info=user_info, context=history[:-1])
        completion = self.feed_LLM(prompt)
        result = ''
        for chunk in completion:
            result += chunk.choices[0].delta.content
        match = re.search(r'```json\s*(\{.*\})\s*```', result, re.DOTALL)
        query = json.loads(match.group(1))
        print(query)
        for attr in ['饮食类型', '菜系', '中西餐']:
            if query[attr] == 0:
                query[attr] = slice(None)
        if query['价格'] != '未加限定':
            filtered_items = self.items[(self.items['price']>=query['价格'][0]) & (self.items['price']<=query['价格'][1])]
        else:
            filtered_items = self.items
        indexes = (query['饮食类型'], query['菜系'], query['中西餐'], query['不辣'], query['微辣'], query['中辣'], query['特辣'])
        filtered_items = filtered_items.loc[indexes]
        index = faiss.IndexFlatL2(len(soft_constraints))
        vectors = filtered_items[soft_constraints].to_numpy()
        index.add(vectors)
        query_vector = np.array(list(query.values())[8:]).reshape(1,-1)
        print(query_vector.shape, vectors.shape)
        distances, indices = index.search(query_vector, 5)
        ranked_items = filtered_items.iloc[indices[0]]

        return self.items[self.items['id'].isin(ranked_items['id'].to_list())]['food_name'].to_list()'''