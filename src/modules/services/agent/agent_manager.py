# AgentManager: 管理多个 agent 实例，每个实例对应一个 sessionid
from typing import Dict
from src.modules.services.agent.agent import Agent
from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.service_basis.basis.tool import Tool
from src.modules.services.business.record_bussiness import DialogueRecordBusiness

class AgentManager:
    def __init__(self, tools: Registry, record_business: DialogueRecordBusiness, prompt_template: str):
        self._agents: Dict[str, Agent] = {}
        self._tools = tools
        self._record_business = record_business
        self._prompt_template = prompt_template

    def get_agent(self, user_id: str, sessionid: str) -> Agent:
        if sessionid not in self._agents:
            self._agents[sessionid] = Agent(user_id, sessionid, self._record_business, self._tools, self._prompt_template)
        return self._agents[sessionid]

    def remove_agent(self, sessionid: str):
        if sessionid in self._agents:
            del self._agents[sessionid]

    def has_agent(self, sessionid: str) -> bool:
        return sessionid in self._agents
