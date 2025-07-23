from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam
from typing import Iterable

def feed_LLM(prompt: str) -> Iterable:
        """
        根据提示词生成回复
        :param prompt: 输入大模型的提示词
        :return: 返回一个生成器对象，迭代获取每个流式响应块（chunk），每个chunk为OpenAI API的响应对象
        """
        client = OpenAI(
            api_key="sk-8f86f5e9b0b34e8a9e7319e68f99787e",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        messages = [ChatCompletionUserMessageParam(role="user", content=prompt)]
        completion = client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            stop="Observation",
            stream=True,
            stream_options={"include_usage": False}
        )
        return completion


def feed_and_gether_LLM(prompt: str) -> str:
    """
    根据提示词生成回复，并将所有流式响应块合并为一个字符串
    :return: 返回一个字符串，包含所有流式响应块的内容
    """
    completion_generator = feed_LLM(prompt)
    completion = ''
    for chunk in completion_generator:
        completion += chunk.choices[0].delta.content
    return completion