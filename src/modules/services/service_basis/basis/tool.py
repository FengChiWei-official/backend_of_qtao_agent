from src.modules.service_basis.user_info import UserInfo
from abc import ABC, abstractmethod

class Tool(ABC):
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"""
            "name" = {self.name}, 
            "description" = {self.description}
        """

    def __str__(self):
        return self.__repr__()
    

    @abstractmethod
    def __call__(self, parameter: dict, user_info: UserInfo, history: list):
        """
        子类必须实现该方法，参数签名固定
        :param parameter: 查询参数
        :param user_info: 用户信息
        :param history: 历史记录
        :return: 查询结果
        """
        raise NotImplementedError("子类必须实现这个方法")