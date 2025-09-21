"""
This package exports the core business logic, services, and handlers
for the application, simplifying access to key components.
"""

from .handler import (
    conversation_router,
    record_router,
    user_router,
    get_user_business,
    get_conversation_business,
    get_record_business,
    get_agent_manager,
    check_ownership_function_generator,
)
from .services import (
    # Business services
    UserBusiness,
    ConversationBusiness,
    DialogueRecordBusiness,
    # Agent services
    AgentManager,
    prompt,
    # Tool services
    MealService,
    TicketQuery,
    TicketQueryMappingDate,
    WeatherQuery,
    TravelPlan,
    Registry,
)

__all__ = [
    # Routers
    "conversation_router",
    "record_router",
    "user_router",
    # Business Logic
    "UserBusiness",
    "ConversationBusiness",
    "DialogueRecordBusiness",
    # Agent
    "AgentManager",
    "prompt",
    # Tools
    "MealService",
    "TicketQuery",
    "TicketQueryMappingDate",
    "WeatherQuery",
    "TravelPlan",
    "Registry",
    # Dependency injectors
    "get_user_business",
    "get_conversation_business",
    "get_record_business",
    "get_agent_manager",
    "check_ownership_function_generator",
]