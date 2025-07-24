import pytest
from unittest.mock import MagicMock, patch
from src.modules.services.agent.agent import Agent
from src.modules.services.service_basis.basis.tool import Tool
from src.modules.services.service_basis.ToolRegistry import Registry

class EchoTool(Tool):
    def __init__(self):
        super().__init__(name="echo", description="Echo tool for test")
    def __call__(self, parameter, user_info, history):
        self.last_call = (parameter, user_info, history)
        return "tool_output"

@pytest.fixture
def mock_dependencies():
    # Mock DialogueRecordBusiness
    mock_record_business = MagicMock()
    # Mock Registry
    mock_registry = MagicMock()
    mock_registry.list_services.return_value = ["mock_tool"]
    mock_tool = MagicMock()
    mock_tool.__call__ = MagicMock(return_value="tool_output")
    mock_registry.get_service.return_value = mock_tool
    # Mock prompt template
    prompt_template = "Prompt: {tools_description} {date} {tools_names}"
    return {
        "user_id": "test_user",
        "conversation_id": "conv_1",
        "record_bussiness": mock_record_business,
        "tools": mock_registry,
        "prompt_template": prompt_template
    }

@patch("src.modules.services.agent.state.State._State__push_to_history", return_value=None)
@patch("src.modules.services.agent.agent.gather_llm_output")
@patch("src.modules.services.service_basis.user_info.UserInfo.parse_user_info", return_value=[{"mock": "data"}])
@patch("src.modules.services.agent.state.State.generate_query_for_llm", return_value=[{"role": "user", "content": "你好"}])
def test_agent_call(mock_generate_query, mock_parse_user_info, mock_gather_llm_output, mock_push_history, mock_dependencies):
    # Mock llm: first call returns action, second call returns final answer
    mock_llm = MagicMock(side_effect=[
        "Thought: think\nAction: mock_tool\nAction Input: {\"param\": 1}",
        "Thought: t\nFinal Answer: {\"answer\": \"ok\", \"picture\": []}"
    ])
    mock_gather_llm_output.return_value = mock_llm

    agent = Agent(**mock_dependencies)
    result = agent("你好")
    assert isinstance(result, dict)
    assert result["answer"] == "ok"

def test_agent_tool_call(monkeypatch):
    import src.modules.services.service_basis.user_info as user_info_mod
    monkeypatch.setattr(user_info_mod.UserInfo, "parse_user_info", lambda self: [{"mock": "data"}])
    registry = Registry()
    echo_tool = EchoTool()
    registry.register(echo_tool)
    mock_record_business = MagicMock()
    prompt_template = "Prompt: {tools_description} {date} {tools_names}"
    agent = Agent(
        user_id="test_user",
        conversation_id="conv_1",
        record_bussiness=mock_record_business,
        tools=registry,
        prompt_template=prompt_template
    )
    llm_outputs = [
        "Thought: think\nAction: echo\nAction Input: {\"msg\": \"hi\"}",
        "Thought: t\nFinal Answer: {\"answer\": \"ok\", \"picture\": []}"
    ]
    monkeypatch.setattr(agent, "llm", lambda x: llm_outputs.pop(0))
    monkeypatch.setattr("src.modules.services.agent.state.State._State__push_to_history", lambda self: None)
    result = agent("你好")
    assert isinstance(result, dict)
    assert result["answer"] == "ok"
    assert hasattr(echo_tool, "last_call")
    assert echo_tool.last_call[0] == {"msg": "hi"}

if __name__ == "__main__":
    pytest.main([__file__])


