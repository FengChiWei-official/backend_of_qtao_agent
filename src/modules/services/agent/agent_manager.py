# AgentManager: 管理 agent 实例的创建和使用
# 修改说明：移除内存缓存 (_agents)，改为每次请求创建新的 Agent 实例，以实现无状态化。
# 这解决了在多 worker 部署下的状态不一致问题，并避免了内存泄漏风险。

from typing import Dict, Generator
from datetime import datetime
from src.modules.services.agent.agent import Agent
from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.business.record_bussiness import DialogueRecordBusiness

class AgentManager:
    def __init__(self, tools: Registry, record_business: DialogueRecordBusiness, prompt_template: str):
        self._tools = tools
        self._record_business = record_business
        self._prompt_template = prompt_template

    def call_agent(self, user_id: str, sessionid: str, query: str) -> dict:
        """
        创建并使用一个新的 agent 实例来处理请求（非流式）。
        Agent 是无状态的，或者说它的状态完全由数据库中的历史记录决定。
        每次请求都从数据库重新加载上下文，处理完毕后销毁实例。
        
        :param user_id: 用户ID
        :param sessionid: 会话ID
        :param query: 用户输入
        :return: Agent 处理结果字典
        """
        # 创建新的 Agent 实例
        agent = Agent(user_id, sessionid, self._record_business, self._tools, self._prompt_template)
        
        # 直接调用 agent 处理逻辑
        # 由于每次都是新实例，不需要额外的锁机制（除非 Agent 内部有共享资源的并发写操作，
        # 但通常每个请求都在独立的线程/协程中处理，且 Agent 实例是局部的）
        return agent(query)

    def stream_agent(self, user_id: str, sessionid: str, query: str) -> Generator:
        """
        创建并使用一个新的 agent 实例来处理请求（流式）。
        逐步生成事件，允许前端实时显示结果。
        
        :param user_id: 用户ID
        :param sessionid: 会话ID
        :param query: 用户输入
        :return: 生成器，逐步产生事件字典 (type, content)
        """
        # 创建新的 Agent 实例
        agent = Agent(user_id, sessionid, self._record_business, self._tools, self._prompt_template)
        
        # 返回流式生成器
        return agent.stream_call(query)

