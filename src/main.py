import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.modules import *
from src.utils import BaseResponse, root_path
from config import ConfigLoader
from fastapi.middleware.cors import CORSMiddleware

PATH_TO_ROOT = root_path.get_root_path()
PATH_TO_CONFIG = PATH_TO_ROOT / "config" / "config.yaml"

if __name__ == "__main__":
    import uvicorn
    server_config = ConfigLoader(PATH_TO_CONFIG).get_server_config()

    # 日志级别兼容字符串和int
    log_level_str = server_config.get("log_level", "info")
    log_level = getattr(logging, str(log_level_str).upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format=server_config.get("log_format", "%(asctime)s - %(levelname)s - %(message)s"),
        force=True,
    )
    uvicorn.run(
        "src.app:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("reload", True)

    )








"""
def get_user_business():
    return user_business_instance

def get_conversation_business():
    return conversation_business_instance

def get_record_business():
    return record_business_instance

def get_agent_manager():
    return agent_manager_instance

def main():

    CONFIG = ConfigLoader(PATH_TO_CONFIG)
    db_config = CONFIG.get_db_config()
    server_config_in_main = CONFIG.get_server_config()

    # 日志级别兼容字符串和int
    log_level_str = server_config_in_main.get("log_level", "info")
    log_level = getattr(logging, str(log_level_str).upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format=server_config_in_main.get("log_format", "%(asctime)s - %(levelname)s - %(message)s"),
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting the application...")
    app = FastAPI()

    # 加载配置
    

    # 初始化DAO和业务对象
    
    global user_business_instance
    user_business_instance = UserBusiness(db_config)

    global conversation_business_instance
    conversation_business_instance = ConversationBusiness(db_config)

    global record_business_instance
    record_business_instance = DialogueRecordBusiness(db_config)


    # 注册工具
    registry = Registry()
    registry.register(MealService())
    registry.register(TicketQuery())
    registry.register(WeatherQuery())
    # AgentManager 依赖示例（如需工具和模板请补充）
    global agent_manager_instance
    
    agent_manager_instance = AgentManager(tools=registry, record_business=record_business_instance, prompt_template="")

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_config_in_main.get("cors", {}).get("allow_origins", ["*"]),
        allow_credentials=server_config_in_main.get("cors", {}).get("allow_credentials", True),
        allow_methods=server_config_in_main.get("cors", {}).get("allow_methods", ["*"]),
        allow_headers=server_config_in_main.get("cors", {}).get("allow_headers", ["*"]),
    )
    logger.info("Application started successfully.")
    return app
"""
