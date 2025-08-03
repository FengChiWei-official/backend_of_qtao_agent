
import pytest
from unittest.mock import patch, MagicMock
from src.utils import chatgpt

def make_fake_chunk(content):
    mock_chunk = MagicMock()
    mock_choice = MagicMock()
    mock_delta = MagicMock()
    mock_delta.content = content
    mock_choice.delta = mock_delta
    mock_chunk.choices = [mock_choice]
    return mock_chunk

@patch('src.utils.chatgpt.OpenAI')
def test_feed_LLM_full(mock_openai):
    fake_chunk = make_fake_chunk('hello')
    mock_client = MagicMock()
    mock_completion = iter([fake_chunk])
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai.return_value = mock_client
    history = [{"role": "user", "content": "hi"}]
    result = list(chatgpt.feed_LLM_full(history))
    assert result == [fake_chunk]
    mock_client.chat.completions.create.assert_called_once()

@patch('src.utils.chatgpt.OpenAI')
def test_feed_LLM(mock_openai):
    fake_chunk = make_fake_chunk('world')
    mock_client = MagicMock()
    mock_completion = iter([fake_chunk])
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai.return_value = mock_client
    prompt = "hello"
    result = list(chatgpt.feed_LLM(prompt))
    assert result == [fake_chunk]
    mock_client.chat.completions.create.assert_called_once()

def test_gather_llm_output():
    @chatgpt.gather_llm_output
    def fake_fn():
        yield make_fake_chunk('a')
        yield make_fake_chunk('b')
    output = fake_fn()
    assert output == 'ab'

def test_feed_LLM_full_real():
    history = [{"role": "user", "content": "你好"}]
    result = chatgpt.feed_LLM_full(history)
    chunk = next(iter(result))
    assert hasattr(chunk, "choices")

def test_feed_LLM_real():
    prompt = "你好"
    result = chatgpt.feed_LLM(prompt)
    chunk = next(iter(result))
    assert hasattr(chunk, "choices")

def test_gather_llm_output_real():
    llm = chatgpt.gather_llm_output(chatgpt.feed_LLM)
    prompt = "你好"
    result = llm(prompt)
    completion = result
    assert completion  # Ensure we got some content back
    assert isinstance(completion, str)  # Ensure the output is a string
    assert len(completion) > 0  # Ensure the string is not empty
    print(f"LLM output: {completion}")  # Print the output for debugging

if __name__ == "__main__":
    pytest.main([__file__])