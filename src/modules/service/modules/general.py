from service.user_info import UserInfo
class General:
    """
    通用模块，负责处理通用查询
    """
    def handle_query(self, query: str,  parameter: dict) -> dict:
        """
        处理通用查询
        :param query: 用户查询
        :return: 处理后通用查询的结果
        """
        # 模拟通用查询处理
        return {"response": f"你问的是: {query}"}

    def parse_parameter(self, query: str) -> dict:
        """
        从用户的查询中解析出关键参数
        :param query: 用户的查询文本
        :return: 解析出的参数
        """
        # 示例：根据query解析出参数
        return {"train_number": "G1001"}

    """
    提示词生成模块，将信息转换为适合大语言模型的prompt
    """
    def generate_prompt(self, info: dict) -> str:
        """
        生成适用于大语言模型的prompt
        :param info: 对应意图的具体信息
        :return: 生成的prompt
        """
        return f"请润色下面顾客的查询答案: {info}"

    def supplement_info(self, user_info: UserInfo) -> dict:
        """
        补充通用查询的额外信息
        :param user_info: 用户信息
        :return: 补充的额外信息
        """
        return {"note": "此为通用查询，当前没有特定的建议。"}