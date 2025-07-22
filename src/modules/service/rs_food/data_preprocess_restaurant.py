# -*- coding: utf-8 -*-

import pandas as pd
from tqdm import tqdm
# 引入共享工具模块
from service.rs_food.preprocess_utils import (
    calculate_age, 
    map_to_age_group, 
    extract_province,
    PROVINCE_MAPPING
)

# 兼容容器和本地开发环境，始终从项目根目录定位 dataset/food/user.csv 和 restaurant.csv
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
user_file_path = project_root / 'dataset' / 'food' / 'user.csv'
item_file_path = project_root / 'dataset' / 'food' / 'restaurant.csv'
user_df = pd.read_csv(user_file_path)
item_df = pd.read_csv(item_file_path)
# 将 province_id、city_id 和 restaurant_id 列连接成新的 'id' 列
item_df['id'] = item_df['province_id'].astype(str) + '_' + item_df['city_id'].astype(str) + '_' + item_df['restaurant_id'].astype(str)

# 删除原有的 province_id, city_id, restaurant_id 列
item_df = item_df.drop(columns=['city_id', 'restaurant_id', 'province_id','restaurant_name','image_name'])

# 使用列映射字典来重命名列
item_df = item_df.rename(columns=PROVINCE_MAPPING)

# 提取用户的出生地省份
user_df['province'] = user_df['出生地'].apply(extract_province)
# 为每个用户计算年龄并映射到年龄段
user_df['age'] = user_df['出生日期'].apply(calculate_age)
user_df['age_group'] = user_df['age'].apply(map_to_age_group)

# 创建一个新的 DataFrame 存储评分数据
rating_data = []

# 为每个用户生成评分
for index, user in tqdm(user_df.iterrows(),
                        total=len(user_df), desc="generate interaction", unit="user"):
    user_id = user['身份证号码']
    province = user['province']
    age_group = user['age_group']

    # 查找与用户省份匹配的食物数据列
    if province and province in item_df.columns:
        region_avg_rating = item_df[province]
        # 为该用户生成评分，假设用户对每个食物评分等于该地区的平均评分
        for food_id, rating in region_avg_rating.items():
            # 使用食物表中的 'id' 作为 item_id
            item_id = item_df.loc[food_id, 'id']
            rating_data.append([user_id, item_id, rating])

        # 查找与用户省份+年龄匹配的食物数据列
        if age_group and age_group in item_df.columns:
            age_group_avg_rating = item_df[age_group]

            # 为该用户生成评分，假设用户对每个食物评分等于该地区的平均评分
            for food_id, rating in region_avg_rating.items():
                # 使用食物表中的 'id' 作为 item_id
                item_id = item_df.loc[food_id, 'id']
                age_rating = age_group_avg_rating[food_id]
                # 同一个食物年龄和地区的评分差距小于1，则认可这个评分
                if abs(rating - age_rating) <= 1:
                    rating_data.append([user_id, item_id, age_rating])

# 将评分数据转换为 DataFrame
rating_df = pd.DataFrame(rating_data, columns=['user_id:token', 'item_id:token', 'rating:float'])

# 随机采样 90% 的数据
rating_df = rating_df.sample(frac=0.9, random_state=42)  # 设置 random_state 以保证每次运行结果相同

# 显示生成的评分数据
print("生成的交互数据：")
print(rating_df.head())

#todo: check the dataset
# 可以将结果保存为新的 CSV 文件
output_file_path = project_root / 'dataset' / 'china-restaurant' / 'china-restaurant.inter'
rating_df.to_csv(output_file_path, sep='\t', index=False)