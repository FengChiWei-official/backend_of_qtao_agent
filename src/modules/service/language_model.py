import time
import requests
import aiohttp
import json
from typing import Optional, Callable, Awaitable, Dict, Any

class LanguageModel:
    """
    大语言模型模块，负责生成最终的回复
    """
    def __init__(self):
        self.headers = {
            "Authorization": "Bearer sk-8f86f5e9b0b34e8a9e7319e68f99787e",
            "Content-Type": "application/json"
        }
        # 修正API端点URL格式
        self.url = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
        self.model = "qwen-max"
        
    def _get_request_body(self, prompt: str, stream: bool = False) -> dict:
        """
        构建API请求体
        :param prompt: 提示词
        :param stream: 是否使用流式响应
        :return: 请求体字典
        """
        return {
            "messages": [
                {"role": "user", "content": f"{prompt}"}
            ],
            "model": self.model,
            "temperature": 0.01,
            "max_tokens": 2000,
            "stream": stream,
            "stop": ["Observation:"],
        }
    
    def generate_response(self, prompt: str) -> str:
        """
        生成基于prompt的回复
        :param prompt: 生成回复所需的prompt
        :return: 大语言模型生成的回复
        """
        start_time = time.time()
        body = self._get_request_body(prompt)
        
        _response = requests.post(self.url, json=body, headers=self.headers)
        _response = _response.json()
        
        end_time = time.time()
        print(f'回答耗时: {end_time - start_time}')

        return _response['choices'][0]['message']['content']

    async def generate_response_async(self, prompt: str, stream_to_client_callback: Optional[Callable[[str], Awaitable[None]]] = None) -> str:
        """
        异步生成基于prompt的回复，支持流式输出
        :param prompt: 生成回复所需的prompt
        :param stream_to_client_callback: 可选的流式回调函数，用于将响应块传输给客户端
        :return: 大语言模型生成的完整回复
        """
        start_time = time.time()
        
        # 如果提供了流式回调，则启用流式模式
        is_streaming = stream_to_client_callback is not None
        body = self._get_request_body(prompt, stream=is_streaming)
        accumulated_response = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=body, headers=self.headers) as response:
                    if response.status != 200:
                        error_message = await response.text()
                        print(f"API错误: {response.status}, 响应内容: {error_message}")
                        return f"API调用失败，状态码: {response.status}"
                    
                    # 处理流式响应
                    if is_streaming:
                        async for line in response.content:
                            if line:
                                decoded_line = line.decode('utf-8').strip()
                                if decoded_line and decoded_line.startswith('data:'):
                                    data_json = decoded_line[5:].strip()  # 移除 "data:" 前缀
                                    if data_json != "[DONE]":  # API流式传输结束标记
                                        try:
                                            chunk_data = json.loads(data_json)
                                            # 根据API返回格式提取内容
                                            if 'choices' in chunk_data and chunk_data['choices']:
                                                if 'delta' in chunk_data['choices'][0]:
                                                    content = chunk_data['choices'][0]['delta'].get('content', '')
                                                elif 'text' in chunk_data['choices'][0]:
                                                    content = chunk_data['choices'][0].get('text', '')
                                                else:
                                                    content = ''
                                                
                                                if content:
                                                    # 发送到客户端
                                                    try:
                                                        await stream_to_client_callback(content)
                                                    except Exception as e:
                                                        print(f"流式传输回调异常: {e}")
                                                    
                                                    # 累积完整响应
                                                    accumulated_response.append(content)
                                        except json.JSONDecodeError:
                                            print(f"无法解析流式数据: {data_json}")
                        
                        # 返回累积的完整响应
                        full_response = "".join(accumulated_response)
                    
                    # 处理非流式响应
                    else:
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' not in content_type:
                            error_message = await response.text()
                            print(f"API返回非JSON响应: {content_type}, 内容: {error_message}")
                            return "API返回格式错误，非JSON响应"
                        
                        _response = await response.json()
                        print(f"API Response: {_response}")  # 打印完整响应以便调试
                        
                        # 检查响应是否包含所需的键
                        if 'choices' in _response and len(_response['choices']) > 0:
                            if 'message' in _response['choices'][0] and 'content' in _response['choices'][0]['message']:
                                full_response = _response['choices'][0]['message']['content']
                            else:
                                # 适应可能的不同API响应格式
                                full_response = _response['choices'][0].get('text', '')
                        elif 'response' in _response:  # 某些API可能使用response字段
                            full_response = _response['response']
                        elif 'data' in _response and 'text' in _response['data']:  # 另一种可能的格式
                            full_response = _response['data']['text']
                        else:
                            print(f"无法解析API响应: {_response}")
                            full_response = "API返回格式错误，请检查日志获取详细信息。"
            
            end_time = time.time()
            print(f'回答耗时: {end_time - start_time}')
            
            return full_response
            
        except Exception as e:
            print(f"API调用异常: {e}")
            return f"API调用异常: {e}"

    async def generate_stream_response_async(self, prompt: str):
        """
        异步生成基于prompt的流式回复
        :param prompt: 生成回复所需的prompt
        :yield: 大语言模型生成的流式回复
        """
        start_time = time.time()
        body = self._get_request_body(prompt, stream=True)

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json=body, headers=self.headers) as response:
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line:
                            yield decoded_line  # Stream each chunk of dataset

        end_time = time.time()
        print(f'回答耗时: {end_time - start_time}')


if __name__ == "__main__":
    language_model = LanguageModel()
    while True:
        response = language_model.generate_response(input('用户：'))
        print(response)