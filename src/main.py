import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.modules.handler.conversation_handler import router as conversation_router
from src.modules.handler.record_handler import router as record_router
from src.modules.handler.user_handler import router as user_router
from src.modules.handler.user_handler import BaseResponse
from config.loadConfig import ConfigLoader
from src.modules.dbController.basis.dbSession import DatabaseSessionManager
from src.modules.dbController.dao.user_dao import UserDAO
from src.modules.services.business.user_bussiness import UserBusiness
from src.modules.dbController.dao.conversation_dao import ConversationDAO
from src.modules.services.business.conversation_bussiness import ConversationBusiness
from src.modules.dbController.dao.dialogue_record_dao import DialogueRecordDAO
from src.modules.services.business.record_bussiness import DialogueRecordBusiness
from src.modules.services.agent.agent_manager import AgentManager

def get_user_business():
    return user_business_instance

def get_conversation_business():
    return conversation_business_instance

def get_record_business():
    return record_business_instance

def get_agent_manager():
    return agent_manager_instance

def main():
    logging.basicConfig(
        level=logging.INFO,  # 日志级别
        format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting the application...")
    app = FastAPI()

    # 加载配置
    config = ConfigLoader("config/config.yaml").config
    # 初始化数据库会话管理器
    db_session_manager = DatabaseSessionManager(config)

    # 初始化DAO和业务对象
    user_dao = UserDAO(db_session_manager)
    global user_business_instance
    user_business_instance = UserBusiness(user_dao)

    conversation_dao = ConversationDAO(db_session_manager)
    global conversation_business_instance
    conversation_business_instance = ConversationBusiness(conversation_dao)

    dialogue_record_dao = DialogueRecordDAO(db_session_manager)
    global record_business_instance
    record_business_instance = DialogueRecordBusiness(dialogue_record_dao)

    # AgentManager 依赖示例（如需工具和模板请补充）
    global agent_manager_instance
    agent_manager_instance = AgentManager(tools=None, record_business=record_business_instance, prompt_template="")

    # 注册统一异常处理器
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=BaseResponse(msg=exc.detail, data=None).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=BaseResponse(msg="参数校验失败", data=exc.errors()).model_dump()
        )

    app.include_router(conversation_router)
    app.include_router(record_router)
    app.include_router(user_router)
    # 注入业务依赖
    app.dependency_overrides[get_user_business] = get_user_business
    app.dependency_overrides[get_conversation_business] = get_conversation_business
    app.dependency_overrides[get_record_business] = get_record_business
    app.dependency_overrides[get_agent_manager] = get_agent_manager
    # 其他路由和中间件配置
    logger.info("Application started successfully.")