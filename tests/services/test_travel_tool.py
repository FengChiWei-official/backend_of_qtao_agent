import unittest
import sys
from pathlib import Path

# Add the project root to the Python path
# This is necessary for the imports to work correctly when running the test from the command line
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.modules.services.service_basis.travel_tool.travel_plan import TravelPlan
from src.modules.services.service_basis.user_info import UserInfo

class TestTravelPlan(unittest.TestCase):

    def test_travel_plan_call(self):
        """
        Test the __call__ method of the TravelPlan class.
        """
        # 1. Initialize TravelPlan tool
        travel_plan_tool = TravelPlan()

        # 2. Create a dummy UserInfo object
        # UserInfo requires a user_id, let's use a valid-looking dummy ID.
        dummy_user_id = "510101199003079999" 
        user_info = UserInfo(user_id=dummy_user_id)

        # 3. Define test parameters and history
        test_parameter = {
            "用户需求": "我想从重庆去成都玩三天，预算2000元，喜欢吃辣，想看熊猫。"
        }
        test_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，有什么可以帮你的吗？"},
            {"role": "user", "content": "我想去成都玩"}
        ]

        # 4. Call the tool
        result_plan = travel_plan_tool(test_parameter, user_info, test_history)

        # 5. Assert the results
        self.assertIsNotNone(result_plan, "The returned plan should not be None.")
        self.assertIsInstance(result_plan, dict, "The plan should be a dictionary.")
        
        # You could add more specific assertions here if you know the expected structure of the plan
        print("\n--- Travel Plan Test Result ---")
        print(result_plan)
        print("-----------------------------\n")

if __name__ == '__main__':
    # Add the parent directory of 'tests' to the Python path to resolve module imports
    # This is often needed when running tests directly
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    unittest.main()
