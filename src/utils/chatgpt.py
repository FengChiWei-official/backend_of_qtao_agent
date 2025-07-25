from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam
from typing import Iterable, Callable, Any

def feed_LLM_full(history: list) -> Iterable:
    """
    根据历史记录生成回复
    :param history: 历史记录列表
    :return: 返回一个生成器对象，迭代获取每个流式响应块（chunk），每个chunk为OpenAI API的响应对象
    """
    client = OpenAI(
        api_key="sk-8f86f5e9b0b34e8a9e7319e68f99787e",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    messages = [ChatCompletionUserMessageParam(role=msg["role"], content=msg["content"]) for msg in history]
    completion = client.chat.completions.create(
        model="qwen-max",
        messages=messages,
        stop="Observation",
        stream=True,
        stream_options={"include_usage": False}
    )
    return completion

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


def gather_llm_output(fn):
    """
    装饰器：将返回的流式 LLM 响应聚合为字符串
    """
    def wrapper(*args, **kwargs):
        completion = ''
        for chunk in fn(*args, **kwargs):
            completion += chunk.choices[0].delta.content
        return completion
    return wrapper

