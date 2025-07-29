# AgentManager: 管理多个 agent 实例，每个实例对应一个 sessionid
from typing import Dict
import threading
from datetime import datetime
from src.modules.services.agent.agent import Agent
from src.modules.services.service_basis.ToolRegistry import Registry
from src.modules.services.service_basis.basis.tool import Tool
from src.modules.services.business.record_bussiness import DialogueRecordBusiness

class AgentManager:
    def __init__(self, tools: Registry, record_business: DialogueRecordBusiness, prompt_template: str):
        self._agents: Dict[str, Agent] = {}
        self._last_activate_time: Dict[str, datetime] = {}
        self._tools = tools
        self._record_business = record_business
        self._prompt_template = prompt_template
        self.lock = threading.Lock()
        # 用于清理 agent 的事件
        # 例如在应用关闭时可以设置此事件，通知所有 agent 进行清理
        # 这可以帮助释放资源或保存状态
        self.cleanup_thread = threading.Thread(target=self.cleanup_inactive_agents, daemon=True)
        self.cleanup_thread.start()

    def _get_agent(self, user_id: str, sessionid: str) -> Agent:
        with self.lock:
            if sessionid not in self._agents:
                self._agents[sessionid] = Agent(user_id, sessionid, self._record_business, self._tools, self._prompt_template)
            # 更新最后激活时间
            self._last_activate_time[sessionid] = datetime.now()
            return self._agents[sessionid]

    def _remove_agent(self, sessionid: str):
        with self.lock:
            if sessionid in self._agents:
                del self._agents[sessionid]

    def get_and_use_agent(self, user_id: str, sessionid: str, query: str) -> dict:
        """
        获取并使用 agent 实例
        :param user_id: 用户ID
        :param sessionid: 会话ID
        :return: Agent 实例
        """
        agent = self._get_agent(user_id, sessionid)
        with agent.lock:
            ans = agent(query)
        return ans
    
    def cleanup_inactive_agents(self, timeout: int = 300):
        """
        清理超过指定时间未激活的 agent 实例
        :param timeout: 超时时间，单位为秒
        """
        current_time = datetime.now()
        with self.lock:
            for sessionid, last_time in list(self._last_activate_time.items()):
                if (current_time - last_time).total_seconds() > timeout:
                    self._remove_agent(sessionid)
                    del self._last_activate_time[sessionid]
