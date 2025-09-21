import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.modules import (
    MealService, TicketQuery, WeatherQuery, TravelPlan, Registry,
    UserBusiness, ConversationBusiness, DialogueRecordBusiness,
    AgentManager, prompt,
    get_user_business as handler_get_user_business,
    get_conversation_business as handler_get_conversation_business,
    get_agent_manager as handler_get_agent_manager,
    check_ownership_function_generator as handle_check_ownership_function_generator,
    get_record_business as handler_get_record_business,
    conversation_router, record_router, user_router
)
from src.utils import BaseResponse, root_path
from config import ConfigLoader
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from src.utils.auth_dependency import get_current_user as auth_get_current_user
import traceback

PATH_TO_ROOT = root_path.get_root_path()
PATH_TO_CONFIG = PATH_TO_ROOT / "config"/"config.yaml"
CONFIG = ConfigLoader(PATH_TO_CONFIG)
db_config = CONFIG.get_db_config()
server_config = CONFIG.get_server_config()

logger = logging.getLogger(__name__)
logger.info("Starting the application...")
app = FastAPI()



def check_ownership_function_generator():
    return user_business_instance.check_conversation_ownership



# 初始化DAO和业务对象
user_business_instance = UserBusiness(db_config)
conversation_business_instance = ConversationBusiness(db_config)
record_business_instance = DialogueRecordBusiness(db_config)

# 注册工具
mealservice_name = "订餐服务"
mealservice_desc = '''
订餐服务：本接口用于从数据库中匹配最符合用户偏好与要求的餐厅或菜品。接口输入格式：该接口无需输入参数，填 {"parameter": {}} 即可。
接口输出格式：返回一个列表，包含推荐的餐厅或菜品信息，每个元素是一个字典，包含餐厅或菜品的详细信息 e.g.最终推荐列表为：[{'food_id': '31_18_2', 'food_name': '皇堡'}, {'food_id': '2_16_9', 'food_name': '原味圣代'}, {'food_id': '15_11_6', 'food_name': '米粉'}]
note: 调用了这个工具就要输出 images = ["<图片链接1>", "<图片链接2>", ..., "<图片名称1>", "<图片名称2>", ...]，其中每个图片链接都是一个字符串，表示餐厅或菜品的图片链接
     链接格式： images/<菜品id>.jpg， 也就是接口输出中的"\\d_\\d_\\d"
     图片名称： 就是对应菜品的名字，比如假如你观察到observation 有一句： 推荐小笼包（2-3-4），你就要输出 images = ["/images/2-3-4.jpg", "小笼包"]，注意图片链接和图片名称之间用逗号分隔开来
。'''
meal_top_k = 3
registry = Registry()
registry.register(MealService())
registry.register(TicketQuery())
registry.register(WeatherQuery())
registry.register(TravelPlan())
agent_manager_instance = AgentManager(tools=registry, record_business=record_business_instance, prompt_template=prompt)



# 注册统一异常处理器
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    import traceback
    msg = exc.detail.get("message") if isinstance(exc.detail, dict) else str(exc.detail)
    if msg is None:
        msg = ""
    tb = traceback.format_exc()
    logger.error(f"HTTPException: {exc.status_code} {msg} | detail: {exc.detail}\nTraceback: {tb}")
    return JSONResponse(
        status_code=exc.status_code,
        content=BaseResponse(
            msg=msg,
            data={
                "type": str(type(exc)),
                "status_code": exc.status_code,
                "detail": exc.detail,
                "exception": str(exc),
                "traceback": tb
            }
        ).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"ValidationError: {exc.errors()} | body: {await request.body()}", stack_info=True)
    return JSONResponse(
        status_code=422,
        content=BaseResponse(
            msg="参数校验失败",
            data={
                "errors": exc.errors(),
                "body": (await request.body()).decode("utf-8")
            }
        ).model_dump()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"Unhandled Exception: {str(exc)}\nTraceback: {tb}", stack_info=True)
    return JSONResponse(
        status_code=500,
        content=BaseResponse(
            msg="服务器内部错误",
            data={
                "error": str(exc),
                "traceback": tb
            }
        ).model_dump()
    )

app.include_router(conversation_router)
app.include_router(record_router)
app.include_router(user_router)
# 注入业务依赖
app.dependency_overrides[handler_get_user_business] = lambda: user_business_instance
app.dependency_overrides[handler_get_conversation_business] = lambda: conversation_business_instance
app.dependency_overrides[handler_get_record_business] = lambda: record_business_instance
app.dependency_overrides[handler_get_agent_manager] = lambda: agent_manager_instance
app.dependency_overrides[handle_check_ownership_function_generator] = check_ownership_function_generator
# 其他路由和中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.get("cors", {}).get("allow_origins", ["*"]),
    allow_credentials=server_config.get("cors", {}).get("allow_credentials", True),
    allow_methods=server_config.get("cors", {}).get("allow_methods", ["*"]),
    allow_headers=server_config.get("cors", {}).get("allow_headers", ["*"]),
)
# 挂载静态文件目录（用于图片访问），不会出现在 OpenAPI 文档
app.mount(
    "/images",
    StaticFiles(directory=PATH_TO_ROOT / "static" / "images"),
    name="images"
)
# 说明：此路由仅用于静态资源访问，不会在 FastAPI 自动生成的接口文档中显示。
logger.info("Application started successfully.")


