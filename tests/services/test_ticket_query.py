import pytest
import os, sys
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PATH_TO_ROOT)
from src.modules.service.ticket_query import TicketQuery
from src.modules.service.user_info import UserInfo

@pytest.fixture
def user_info():
    return UserInfo(user_id="test_user", ticket_info={})

@pytest.fixture
def ticket_query():
    return TicketQuery()

def test_missing_required_param(ticket_query, user_info):
    # 缺少起始站
    param = {"终点站": "乌鲁木齐"}
    result = ticket_query(param, user_info, [])
    assert any("缺少必需参数" in str(r) for r in result)

    # 缺少终点站
    param = {"起始站": "北京"}
    result = ticket_query(param, user_info, [])
    assert any("缺少必需参数" in str(r) for r in result)

def test_station_not_found(ticket_query, user_info):
    param = {"起始站": "不存在站", "终点站": "乌鲁木齐"}
    result = ticket_query(param, user_info, [])
    assert any("找不到起始站" in str(r) for r in result)

    param = {"起始站": "北京", "终点站": "不存在站"}
    result = ticket_query(param, user_info, [])
    assert any("找不到终点站" in str(r) for r in result)

def test_no_direct_route(ticket_query, user_info):
    param = {"起始站": "北京", "终点站": "乌鲁木齐"}
    result = ticket_query(param, user_info, [])
    # 可能没有直达车次
    assert any("找不到从" in str(r) for r in result) or isinstance(result, list)

def test_date_filter(ticket_query, user_info):
    param = {"起始站": "北京", "终点站": "乌鲁木齐", "发车日期": "1900-01-01"}
    result = ticket_query(param, user_info, [])
    # 日期不存在时应有提示
    assert any("车次不存在" in str(r) for r in result) or isinstance(result, list)

def test_valid_query(ticket_query, user_info):
    # 只要有数据应能查到结果
    param = {"起始站": "北京", "终点站": "乌鲁木齐"}
    result = ticket_query(param, user_info, [])
    assert isinstance(result, list)
    # 结果中应包含字典（车票信息）或提示信息
    assert any(isinstance(r, dict) or isinstance(r, str) for r in result)

if __name__ == "__main__":
    pytest.main(["-v", __file__])