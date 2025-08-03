import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from src.modules.handler.record_handler import router, ChatRequest

# 模拟依赖
class DummyAgentManager:
    def get_and_use_agent(self, user_id, session_id, query):
        return {"reply": f"user {user_id} session {session_id} query {query}"}

def dummy_get_current_user():
    return "test_user"

def dummy_ownership_checker(user_id, session_id):
    # 只有 session_id == "valid_session" 时有权限
    return session_id == "valid_session"

def override_get_agent_manager():
    return DummyAgentManager()

def override_check_ownership_function_generator():
    return dummy_ownership_checker

app = FastAPI()
app.include_router(router)
from src.modules.handler.record_handler import get_current_user, get_agent_manager, check_ownership_function_generator
app.dependency_overrides = {
    get_current_user: dummy_get_current_user,
    get_agent_manager: override_get_agent_manager,
    check_ownership_function_generator: override_check_ownership_function_generator,
}

client = TestClient(app)

def test_chat_ownership_success():
    data = {"session_id": "valid_session", "query": "hello"}
    response = client.post("/api/v1/chat", json=data)
    assert response.status_code == 200
    assert response.json()["msg"] == "success"
    assert "reply" in response.json()["data"]

def test_chat_ownership_forbidden():
    data = {"session_id": "invalid_session", "query": "hello"}
    response = client.post("/api/v1/chat", json=data)
    assert response.status_code == 403
    assert response.json()["detail"] == "没有权限访问该会话"

if __name__ == "__main__":
    pytest.main([__file__])
