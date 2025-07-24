import pytest
import pandas as pd
import numpy as np
import sys, os
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(PATH_TO_ROOT)
from src.modules.services.service_basis.meal_service import MealService

# 真实服务测试，不使用 mock

def test_init():
    service = MealService()
    assert isinstance(service.items, pd.DataFrame)
    assert len(service.item_names) > 0

def test_recommend():
    service = MealService()
    user_info = {'性别': '男'}
    history = ['user', 'assistant']
    result = service.recommend(user_info, history)
    assert isinstance(result, list)
    assert len(result) > 0

def test_retrieve():
    service = MealService()
    candidates = service.item_names[:1]
    result = service.retrieve(candidates)
    assert isinstance(result, list)
    assert any('food_name' in item for item in result)

def test_judge():
    service = MealService()
    candidates = service.item_names[:1]
    retrieved = service.retrieve(candidates)
    result = service.judge(candidates, retrieved)
    assert isinstance(result, dict)
    assert candidates[0] in result
    assert 'food_name' in result[candidates[0]]

def test_encode():
    service = MealService()
    candidates = service.item_names[:1]
    result = service.encode(candidates)
    assert isinstance(result, dict)
    assert len(result) > 0
    #assert "nm" in candidates
    #assert "nm" in result

def test_knn():
    service = MealService()
    # 使用烤鸭的特征模板
    query = {
  "饮食类型": 1,
  "菜系": 1,
  "中西餐": 1,
  "不辣": 1,
  "微辣": 0,
  "中辣": 0,
  "特辣": 0,
  "价格": [200, 500],
  "北京": 5,
  "天津": 4,
  "河北": 3,
  "山西": 3,
  "内蒙古": 3,
  "辽宁": 3,
  "吉林": 3,
  "黑龙江": 3,
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
  "儿童": 4,
  "青年": 5,
  "成年人": 5,
  "中年人": 5,
  "老年人": 4,
  "早餐": 1,
  "午餐": 4,
  "晚餐": 5,
  "下午茶": 1,
  "夜宵": 2,
  "男": 5,
  "女": 5,
  "春": 5,
  "夏": 5,
  "秋": 5,
  "冬": 5
}
    result = service.KNN(query)
    assert 'food_name' in result

def test_feed_LLM():
    service = MealService()
    prompt = "你好，请用一句话介绍烤鸭。"
    # feed_LLM 返回一个生成器，取第一个chunk
    completion = service.feed_LLM(prompt)
    first_chunk = next(completion)

    # 检查返回类型和内容
    assert hasattr(first_chunk, 'choices')
    assert hasattr(first_chunk.choices[0], 'delta')
    assert isinstance(first_chunk.choices[0].delta.content, str)

    for chunk in completion:
        assert hasattr(chunk, 'choices')
        assert hasattr(chunk.choices[0], 'delta')

if __name__ == "__main__":

    pytest.main([__file__])
    print("All tests passed!")