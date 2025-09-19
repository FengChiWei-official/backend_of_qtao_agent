from src.utils.root_path import get_root_path
PATH_TO_ROOT = get_root_path()
import sys
if str(PATH_TO_ROOT) not in sys.path:
    sys.path.append(str(PATH_TO_ROOT))
# 路径常量集中管理
DATASET_ITEM_PATH = PATH_TO_ROOT / 'dataset' / 'meal_service' / 'item.csv'

import pandas as pd
import re, json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein
import time

from src.modules.services.service_basis.basis.tool import Tool
from src.modules.services.service_basis.user_info import UserInfo
import re
import json
from typing import Any
from src.utils.chatgpt import feed_LLM


import logging
logger = logging.getLogger(__name__)





recommend_prompt = \
'''
【任务】 基于用户信息和历史对话,总结用户的特点，然后重点关注最后历史对话的最后一个问询，推荐用户最有可能想要的{top_k}个餐食
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

mealservice_desc = '''
订餐服务：本接口用于从数据库中匹配最符合用户偏好与要求的餐厅或菜品。接口输入格式：该接口无需输入参数，填 {"parameter": {}} 即可。
接口输出格式：返回一个列表，包含推荐的餐厅或菜品信息，每个元素是一个字典，包含餐厅或菜品的详细信息 e.g.最终推荐列表为：[{'food_id': '31_18_2', 'food_name': '皇堡'}, {'food_id': '2_16_9', 'food_name': '原味圣代'}, {'food_id': '15_11_6', 'food_name': '米粉'}]
note: 调用了这个工具就要输出 images = ["<图片链接1>", "<图片链接2>", ..., "<图片名称1>", "<图片名称2>", ...]，其中每个图片链接都是一个字符串，表示餐厅或菜品的图片链接
     链接格式： images/<菜品id>.jpg， 也就是接口输出中的"\\d_\\d_\\d"
     图片名称： 就是对应菜品的名字，比如假如你观察到observation 有一句： 推荐小笼包（2-3-4），你就要输出 images = ["/images/2-3-4.jpg", "小笼包"]，注意图片链接和图片名称之间用逗号分隔开来
。'''

soft_constraints = ["Beijing", "Tianjin", "Hebei", "Shanxi", "Nei Mongol", "Liaoning", "Jilin", "Heilongjiang", "Shanghai", "Jiangsu", "Zhejiang", "Anhui", "Fujian", "Jiangxi", "Shandong", "Henan", "Hubei", "Hunan", "Guangdong", "Guangxi", "Hainan", "Chongqing", "Sichuan", "Guizhou", "Yunnan", "Xizang", "Shanxi2", "Gansu", "Qinghai", "Ningxia", "Xinjiang", "child", "teenager", "adult", "middle-ager", "elderly", "breakfast", "lunch", "dinner", "afternoon-tea", "night-snack", "male", "female", "spring", "summer", "autumn", "winter"]

mapping = {
    'Beijing': '北京', 'Tianjin': '天津', 'Hebei': '河北', 'Shanxi': '山西', 'Nei Mongol': '内蒙古', 'Liaoning': '辽宁', 'Jilin': '吉林', 'Heilongjiang': '黑龙江', 'Shanghai': '上海', 'Jiangsu': '江苏', 'Zhejiang': '浙江', 'Anhui': '安徽', 'Fujian': '福建', 'Jiangxi': '江西', 'Shandong': '山东', 'Henan': '河南', 'Hubei': '湖北', 'Hunan': '湖南', 'Guangdong': '广东', 'Guangxi': '广西', 'Hainan': '海南', 'Chongqing': '重庆', 'Sichuan': '四川', 'Guizhou': '贵州', 'Yunnan': '云南', 'Xizang': '西藏', 'Shanxi2': '陕西', 'Gansu': '甘肃', 'Qinghai': '青海', 'Ningxia': '宁夏', 'Xinjiang': '新疆',
    'child': '儿童', 'teenager': '青年', 'adult': '成年人', 'middle-ager': '中年人', 'elderly': '老年人',
    'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐', 'afternoon-tea': '下午茶', 'night-snack': '夜宵',
    'male': '男', 'female': '女',
    'spring': '春', 'summer': '夏', 'autumn': '秋', 'winter': '冬'
}

# 导出按顺序排列的值


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

    def __call__(self, parameter: dict, user_info: UserInfo, history: list):
        import time
        start_time = time.time()
        try:
            t0 = time.time()
            logger.info("[MealService] Start recommendation call.")
            raw_candidates = self.recommend(user_info, history)
            t1 = time.time()
            logger.info(f"[MealService] recommend耗时: {t1-t0:.3f}s, raw_candidates: {raw_candidates}")
        except Exception as e:
            logger.error(f"[MealService] Error in recommend: {e}", exc_info=True)
            raise
        try:
            t2 = time.time()
            retrieved_items = self.retrieve(raw_candidates)
            t3 = time.time()
            logger.info(f"[MealService] retrieve耗时: {t3-t2:.3f}s, retrieved_items: {retrieved_items}")
        except Exception as e:
            logger.error(f"[MealService] Error in retrieve: {e}", exc_info=True)
            raise
        try:
            t4 = time.time()
            judge_result = self.judge(raw_candidates, retrieved_items)
            t5 = time.time()
            logger.info(f"[MealService] judge耗时: {t5-t4:.3f}s, judge_result: {judge_result}")
        except Exception as e:
            logger.error(f"[MealService] Error in judge: {e}", exc_info=True)
            raise
        recommended_list = []
        t6 = time.time()
        for raw_candidate, linked_item in judge_result.items():
            if linked_item is not None:
                recommended_list.append(linked_item)
            else:
                try:
                    encode_start = time.time()
                    unmatched_item = self.encode(raw_candidate)
                    encode_end = time.time()
                    knn_start = time.time()
                    match = self.KNN(unmatched_item)
                    knn_end = time.time()
                    recommended_list.append({'food_id': match['id'], 'food_name': match['food_name']})
                    logger.info(f"[MealService] encode耗时: {encode_end-encode_start:.3f}s, KNN耗时: {knn_end-knn_start:.3f}s, candidate: {raw_candidate}")
                except Exception as e:
                    logger.error(f"[MealService] Error in encode/KNN for {raw_candidate}: {e}", exc_info=True)
        t7 = time.time()
        logger.info(f"[MealService] recommended_list: {recommended_list}")
        logger.info(f"[MealService] Timing: recommend={t1-t0:.3f}s, retrieve={t3-t2:.3f}s, judge={t5-t4:.3f}s, encode+KNN={t7-t6:.3f}s, total={t7-start_time:.3f}s")
        return recommended_list

    def recommend(self, user_info: UserInfo, history: list):
        # 使用大模型进行零样本对话式推荐
        prompt = recommend_prompt.format(top_k=3, user_info=user_info, dialogue=history[-3:])
        completion_generator = feed_LLM(prompt)
        completion = ''
        for chunk in completion_generator:
            completion += chunk.choices[0].delta.content
        match = re.search(r'\s*(\[.*\])\s*', completion, re.DOTALL)
        if match:
            raw_candidates = eval(match.group(1))
            return raw_candidates
        else:
            raise ValueError("No list block found in LLM response.")

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

        df = df.drop_duplicates(subset='food_name')
        retrieved_items = df.to_dict(orient='records')

        return retrieved_items

    def judge(self, raw_candidates: list, retrieved_items: list):
        # 将LLM生成的原始候选物品与实际存在物品进行链接
        prompt = judge_prompt.format(raw_candidates=raw_candidates, retrieved_items=[item['food_name'] for item in retrieved_items])
        completion_generator = feed_LLM(prompt)
        completion = ''
        for chunk in completion_generator:
            completion += chunk.choices[0].delta.content
        
        try:
            # 找到第一个 '{' 和最后一个 '}' 来确定JSON对象的范围
            start_index = completion.find('{')
            end_index = completion.rfind('}')
            if start_index == -1 or end_index == -1 or start_index >= end_index:
                raise ValueError("No valid JSON object boundaries found in LLM response.")

            # 提取括号内的核心字符串
            json_str = completion[start_index : end_index + 1]
            
            # 使用更安全的 json.loads 解析
            judge_result = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            # 如果直接解析失败，则认为可能包含了注释等额外字符，并尝试清理
            # 这个正则表达式会移除所有不在双引号内的、非法的JSON字符（如全角括号）
            cleaned_str = re.sub(r'(?s)"[^"]*"(*SKIP)(*FAIL)|[^\w\s.,{}:"\[\]-]', '', json_str)
            try:
                judge_result = json.loads(cleaned_str)
            except json.JSONDecodeError:
                # 如果清理后仍然失败，则抛出最终异常
                raise ValueError(f"Failed to decode JSON from LLM response after cleaning. Original string: '{json_str}'. Error: {e}")

        for key, val in judge_result.items():
            if val is not None:
                for item in retrieved_items:
                    if item['food_name'] == val:
                        judge_result[key] = item
                        break
        return judge_result

    def encode(self, raw_candidates: list):
        prompt = encoding_prompt.format(items=raw_candidates)
        completion = feed_LLM(prompt)
        result = ''
        for chunk in completion:

            result += chunk.choices[0].delta.content

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

        indexes = (query['饮食类型'], query['菜系'], query['中西餐'])
        filtered_items = filtered_items[(filtered_items['not-spicy']==query['不辣'])|
                                        (filtered_items['slightly-spicy']==query['微辣'])|
                                        (filtered_items['medium-spicy']==query['中辣'])|
                                        (filtered_items['extra-spicy']==query['特辣'])]
        filtered_items = filtered_items.sort_index()
        filtered_items = filtered_items.loc[indexes]

        # vectors = filtered_items[soft_constraints].to_numpy()
        vectors = filtered_items[soft_constraints].fillna(0).to_numpy()
        # vector = np.array([query[k] for k in soft_constraints]).reshape(1, -1)
        vector = np.array(list(query.get(mapping.get(k), 3) for k in soft_constraints)).reshape(1, -1)
        # vector = np.array(list(query.values())[8:]).reshape(1,-1)
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

    


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])

    logging.info("Starting meal service")
    meal_service = MealService()

    # user_info = {"出生地":"上海", "性别":"男", "年龄":"19", "当前日期": "2025-5-11"}
    user_info = UserInfo(user_id="362531200504090911", ticket_info={})
    history = [{'role':'user', 'content':'我想吃点粤菜，你有什么推荐的吗？'}, {'role':'assistant', 'content':'Thought:'}]

    start = time.time()
    meal_service({}, user_info, history)
    end = time.time()
    logger.info(f'耗时：{end-start}')
