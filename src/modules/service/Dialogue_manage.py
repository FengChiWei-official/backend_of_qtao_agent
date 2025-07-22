from enum import Enum
from os import path

path_to_intent = path.join('saved', 'NLU', 'intents.txt')
path_to_slots = path.join('saved', 'NLU', 'slots.txt')

class Act(Enum):
    CHAT = 0
    RESTAURANT_RECOMMEND = 1
    CUISINE_RECOMMEND = 2
    TRAIN_QUERY = 3
    WEATHER_QUERY = 4


class DialogueManage:
    """
    对话管理模块
    功能：根据识别的用户意图和提取到的槽值，决定系统采取的动作
    实现：规则、LLM或专用的DM模型
    """
    def __init__(self):
        '''
        初始化模块
        '''
        # 构建从意图id到意图名的映射        这个小模块集成在哪里比较合适？

        with open(path_to_intent, 'r', encoding='utf-8') as f:
            self.intent_map = f.read().split('\n')

        # 构建从槽位id到槽位名的映射
        with open(path_to_slots, 'r', encoding='utf-8') as f:
            self.slot_map = f.read().split('\n')


    def __call__(self, intent):
        '''
        预测系统采取的动作
        :param intent: 识别出的用户意图
        :return act: 系统将采取的动作（Act枚举）
        '''
        if intent == 49:
            return Act.RESTAURANT_RECOMMEND
        elif intent in [53, 54, 11]:
            return Act.CUISINE_RECOMMEND
        elif intent in [55, 57]:
            return Act.TRAIN_QUERY
        elif intent in [59]:
            return Act.WEATHER_QUERY
        else:
            return Act.CHAT