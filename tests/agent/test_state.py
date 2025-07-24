import pytest
from unittest.mock import MagicMock, patch
from src.modules.services.agent.state import State

@pytest.fixture(autouse=True)
def patch_userinfo():
    with patch('src.modules.services.agent.state.UserInfo') as MockUserInfo:
        mock_userinfo = MagicMock()
        MockUserInfo.return_value = mock_userinfo
        yield

@pytest.fixture
def mock_dependencies():
    mock_record_business = MagicMock()
    mock_record_business.list_records_by_conversation.return_value = []
    return {
        'user_id': 'test_user',
        'conversation_id': 'conv_1',
        'record_bussiness': mock_record_business,
        'prompt_template': 'Prompt: {tools_description} {date} {tools_names}',
        'tools_description': 'ToolDesc',
        'tools_names': ['tool1', 'tool2'],
        'patient': 2
    }

def test_state_init(mock_dependencies):
    state = State(**mock_dependencies)
    assert state is not None

def test_start_thought_action_parse_text_and_save(mock_dependencies):
    state = State(**mock_dependencies)
    raw = 'Thought: think\nAction: act\nAction Input: {"param": 1}'
    getattr(state, '_State__start_thought_action_parse_text_and_save')(raw)
    ta = getattr(state, '_State__thought_action')
    assert ta['thought'] == 'think'
    assert ta['action'] == 'act'
    assert ta['action_input'] == {'param': 1}
    assert ta['observation'] == ''
    assert 'raw' in ta

@pytest.mark.parametrize("raw,expected", [
    # 标准换行
    ('Thought: think\nAction: act\nAction Input: {"param": 1}', {'thought': 'think', 'action': 'act', 'action_input': {'param': 1}}),
    # Windows换行
    ('Thought: think\r\nAction: act\r\nAction Input: {"param": 1}', {'thought': 'think', 'action': 'act', 'action_input': {'param': 1}}),
    # 多余空格
    ('Thought:   think   \nAction:   act   \nAction Input:   {  "param"  : 1  }', {'thought': 'think', 'action': 'act', 'action_input': {'param': 1}}),
    # 少空格
    ('Thought:think\nAction:act\nAction Input:{"param":1}', {'thought': 'think', 'action': 'act', 'action_input': {'param': 1}}),
    # 换行和空格混合
    ('Thought:\n  think\nAction:\n  act\nAction Input:\n  {"param": 1}', {'thought': 'think', 'action': 'act', 'action_input': {'param': 1}}),
    # 只用回车
    ('Thought: think\rAction: act\rAction Input: {"param": 1}', {'thought': 'think', 'action': 'act', 'action_input': {'param': 1}}),
])
def test_start_thought_action_parse_text_and_save_various_whitespace(mock_dependencies, raw, expected):
    state = State(**mock_dependencies)
    getattr(state, '_State__start_thought_action_parse_text_and_save')(raw)
    ta = getattr(state, '_State__thought_action')
    assert ta['thought'] == expected['thought']
    assert ta['action'] == expected['action']
    assert ta['action_input'] == expected['action_input']
    assert ta['observation'] == ''
    assert 'raw' in ta

def test_set_final_answer(mock_dependencies):
    state = State(**mock_dependencies)
    raw = 'Thought: t\nFinal Answer: {"answer": "ok", "picture": ["img1"]}'
    getattr(state, '_State__set_final_answer')(raw)
    fa = getattr(state, '_State__final_answer')
    assert fa['thought'] == 't'
    assert fa['answer'] == 'ok'
    assert fa['picture'] == ['img1']

def test_set_final_answer_no_final_answer(mock_dependencies):
    state = State(**mock_dependencies)
    # 没有Final Answer:字段，只有结构体
    raw = 'Thought: t'  # 没有Final Answer:，应抛出异常
    with pytest.raises(ValueError):
        getattr(state, '_State__set_final_answer')(raw)

def test_set_final_answer_only_json(mock_dependencies):
    state = State(**mock_dependencies)
    # 只有JSON结构体，没有Thought:和Final Answer:前缀
    raw = '{"answer": "qwee", "picture": []}'
    getattr(state, '_State__set_final_answer')(raw)
    fa = getattr(state, '_State__final_answer')
    assert fa['answer'] == 'qwee'
    assert fa['picture'] == []

def test_is_containning_final_answer(mock_dependencies):
    state = State(**mock_dependencies)
    # 标准Final Answer
    assert state._is_containning_final_answer('Final Answer: ...')
    # 只有结构体
    assert state._is_containning_final_answer('{"answer": "qwee", "picture": []}')
    # 只有Thought
    assert not state._is_containning_final_answer('Thought: t')
    # 只有Action
    assert not state._is_containning_final_answer('Action: ...')
    # 嵌入Final Answer关键字
    assert state._is_containning_final_answer('something Final Answer: {"answer": "ok"}')

def test_generate_action_input_for_tools(mock_dependencies):
    state = State(**mock_dependencies)
    setattr(state, '_State__thought_action', {'action': 'a', 'action_input': {'x': 1}})
    action, params = state.generate_action_input_for_tools()
    assert action == 'a'
    assert params == {'x': 1}

def test_load_prompt_template(mock_dependencies):
    state = State(**mock_dependencies)
    prompt = state._load_prompt_template()
    assert 'ToolDesc' in prompt
    assert 'tool1' in prompt and 'tool2' in prompt

def test_generate_query_for_llm(mock_dependencies):
    state = State(**mock_dependencies)
    setattr(state, '_State__query', 'hello')
    setattr(state, '_State__context', [{'raw': 'ctx1'}])
    result = state.generate_query_for_llm()
    assert isinstance(result, list)
    assert any('content' in m for m in result)

def test_generate_final_answer(mock_dependencies):
    state = State(**mock_dependencies)
    setattr(state, '_State__final_answer', {'answer': '42'})
    assert state.generate_final_answer()['answer'] == '42'

@pytest.mark.parametrize("raw,expected", [
    # 标准格式
    ('Thought: t\nFinal Answer: {"answer": "ok", "picture": ["img1"]}', {'thought': 't', 'answer': 'ok', 'picture': ['img1']}),
    # Windows换行
    ('Thought: t\r\nFinal Answer: {"answer": "ok", "picture": ["img1"]}', {'thought': 't', 'answer': 'ok', 'picture': ['img1']}),
    # 多余空格
    ('Thought:   t   \nFinal Answer:   {  "answer"  : "ok" ,  "picture" : [ "img1" ]  }', {'thought': 't', 'answer': 'ok', 'picture': ['img1']}),
    # 少空格
    ('Thought:t\nFinal Answer:{"answer":"ok","picture":["img1"]}', {'thought': 't', 'answer': 'ok', 'picture': ['img1']}),
    # 换行和空格混合
    ('Thought:\n  t\nFinal Answer:\n  {"answer": "ok", "picture": ["img1"]}', {'thought': 't', 'answer': 'ok', 'picture': ['img1']}),
    # 只用回车
    ('Thought: t\rFinal Answer: {"answer": "ok", "picture": ["img1"]}', {'thought': 't', 'answer': 'ok', 'picture': ['img1']}),
])
def test_set_final_answer_various_whitespace(mock_dependencies, raw, expected):
    state = State(**mock_dependencies)
    getattr(state, '_State__set_final_answer')(raw)
    fa = getattr(state, '_State__final_answer')
    assert fa['thought'] == expected['thought']
    assert fa['answer'] == expected['answer']
    assert fa['picture'] == expected['picture']

if __name__ == '__main__':
    pytest.main()