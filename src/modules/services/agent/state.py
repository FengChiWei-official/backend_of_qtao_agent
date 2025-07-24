import sys
from .utils import PATH_TO_ROOT
if str(PATH_TO_ROOT) not in sys.path:
    sys.path.append(str(PATH_TO_ROOT))

from src.modules.services.service_basis.user_info import UserInfo  # Adjust the import path as needed

# Define the State class to manage user state
class State:
    """
    Manages the state of a user.
    Attributes:
        user_id (str): Unique identifier for the user.
        user_info (UserInfo): User information instance.
    
    """

    """
    `dialogue history` is 3 layers:
    - `history`: List of finished conversation records, each mapping to a DialogueRecord row.
    - `context`: List of recent or relevant context records (e.g. last N rounds, or unfinished qtaos).
    - `qta`: Current QTA (question-task-action) state, typically the latest user query or unfinished interaction.
    """
    """
    Example structure based on DialogueRecord table:
    {
        "history": [
            {
                "id": "a1b2c3d4-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "conversation_id": "c1d2e3f4-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "user_id": "u1v2w3x4-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "user_query": "What is the weather like in Beijing?",
                "system_response": "The weather in Beijing is sunny with a high of 30°C.",
                "system_thoughts": "Thought: Check the weather service for current conditions.\nAction: query_weather\nAction Input: {\"city\": \"Beijing\"}\nObservation: The weather in Beijing is sunny with a high of 30°C.\nThought: Provide the weather information to the user.\nFinal Answer: The weather in Beijing is sunny with a high of 30°C.",
                "image_list": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg"
                ],
                "is_removed": False,
                "query_sent_at": "2025-07-23T10:00:00+00:00",
                "response_received_at": "2025-07-23T10:00:01+00:00",
                "created_at": "2025-07-23T10:00:01+00:00"
            },
            # ... more records ...
        ],
        "context": [
            # Typically recent or relevant records, same structure as history
        ],
        "qta": {
            # Current QTA, can be a partial DialogueRecord or a dict like:
            "role": "user",
            "content": "What is the weather like in Beijing?",
            "deep_thinking": {
                "Thought": "What is the weather like in Beijing?",
                "Action": "query_weather",
                "Action Input": {"city": "Beijing"},
                "Observation": None
            }
        }
    }
    """
    def __init__(self, user_id: str, conversation_id:str, dependency_db_controller:None):
        self.__user_id = user_id
        self.__user_info = UserInfo(user_id)
        self.__conversation_id = conversation_id

        self.__dependency_db_controller = None
        self.__history = self.__load_history()

    def __load_history(self):
        return self.__dependency_db_controller.get_records_by_conversation_id(self.__conversation_id)