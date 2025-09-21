from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam
from typing import Iterable, Callable, Any
from src.utils.root_path import get_root_path
from config.loadConfig import ConfigLoader

PATH_TO_ROOT = get_root_path()
PATH_TO_CONFIG = PATH_TO_ROOT / "config" / "config.yaml"
config_loader = ConfigLoader(PATH_TO_CONFIG)


# 缓存 LLM 配置
_llm_config_cache = None
def get_llm_config() -> dict:
    """
    获取本地 LLM 配置
    :return: 返回一个包含 LLM 配置的字典
    """
    global _llm_config_cache
    if _llm_config_cache is None:
        _llm_config_cache = config_loader.get_llm_config()
    return _llm_config_cache


def feed_LLM_full(history: list) -> Iterable:
    """
    根据历史记录生成回复
    :param history: 历史记录列表
    :return: 返回一个生成器对象，迭代获取每个流式响应块（chunk），每个chunk为OpenAI API的响应对象
    """
    llm_config = get_llm_config()
    client = OpenAI(
        api_key=llm_config.get("api_key"),
        base_url=llm_config.get("base_url"),
    )
    messages = [ChatCompletionUserMessageParam(role=msg["role"], content=msg["content"]) for msg in history]
    model = llm_config.get("model") or "qwen3-235b-a22b-instruct-2507"
    stop = llm_config.get("stop")
    create_kwargs = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": False}
    }
    if stop is not None:
        create_kwargs["stop"] = stop
    completion = client.chat.completions.create(**create_kwargs)
    return completion

def feed_LLM(prompt: str) -> Iterable:
        """
        根据提示词生成回复
        :param prompt: 输入大模型的提示词
        :return: 返回一个生成器对象，迭代获取每个流式响应块（chunk），每个chunk为OpenAI API的响应对象
        """
        llm_config = get_llm_config()
        client = OpenAI(
            api_key=llm_config.get("api_key"),
            base_url=llm_config.get("base_url"),
        )
        messages = [ChatCompletionUserMessageParam(role="user", content=prompt)]
        completion = client.chat.completions.create(
            model=llm_config.get("model") or "qwen3-235b-a22b-instruct-2507",
            messages=messages,
            stop=llm_config.get("stop"),
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

