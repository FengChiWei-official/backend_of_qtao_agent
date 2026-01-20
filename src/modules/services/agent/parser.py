import re
import json
from typing import Dict, Tuple, Optional, Any

class LLMOutputParser:
    """
    负责解析 LLM 的输出，提取 Thought, Action, Action Input 或 Final Answer。
    """

    @staticmethod
    def parse_thought_action(text: str) -> Dict[str, Any]:
        """
        解析 Thought, Action, Action Input
        返回字典: {"thought": ..., "action": ..., "action_input": ..., "raw": ...}
        如果解析失败，返回带有 action="ERROR" 的字典
        """
        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.*?)\s*Action:", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 提取 Action
        action_match = re.search(r"Action:\s*(.*?)\s*Action Input:", text, re.DOTALL)
        action = action_match.group(1).strip() if action_match else ""

        if thought == "" or action == "":
            return {
                "thought": text,
                "action": "ERROR",
                "action_input": {},
                "raw": text
            }

        # 提取 Action Input
        input_match = re.search(r"Action Input:\s*(.*)", text, re.DOTALL)
        action_input_str = input_match.group(1).strip() if input_match else ""
        
        parsed_input = {}
        if not action_input_str or action_input_str == "{}":
             parsed_input = {}
        else:
            try:
                # 尝试直接解析
                parsed_input = json.loads(action_input_str)
            except json.JSONDecodeError:
                # 尝试提取 JSON 片段解析
                match = re.search(r"\{.*\}", action_input_str, re.DOTALL)
                if match:
                    try:
                        parsed_input = json.loads(match.group(0))
                    except json.JSONDecodeError:
                        parsed_input = action_input_str
                else:
                    parsed_input = action_input_str

        return {
            "thought": thought,
            "action": action,
            "action_input": parsed_input,
            "raw": text
        }

    @staticmethod
    def parse_final_answer(text: str) -> Dict[str, Any]:
        """
        解析 Final Answer
        返回字典: {"thought": ..., "answer": ..., "picture": ...}
        """
        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.*?)\s*Final Answer:", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 提取 Final Answer JSON
        answer_parts = text.split("Final Answer:")
        answer_str = answer_parts[-1].strip() if len(answer_parts) > 1 else ""
        
        try:
            parsed_answer = json.loads(answer_str)
            answer = parsed_answer.get("answer", "对不起，我无法提供有效的回答。")
            picture = parsed_answer.get("picture", [])
        except json.JSONDecodeError:
            # 如果不是 JSON，尝试直接作为字符串返回，或者抛出异常
            # 这里为了健壮性，如果解析不到 JSON，就把整个字符串当做 answer
            if not answer_str:
                 raise ValueError("无法解析最终答案: 内容为空")
            try:
                 # 尝试提取 JSON
                 match = re.search(r"\{.*\}", answer_str, re.DOTALL)
                 if match:
                    parsed_answer = json.loads(match.group(0))
                    answer = parsed_answer.get("answer", str(parsed_answer))
                    picture = parsed_answer.get("picture", [])
                 else:
                    answer = answer_str
                    picture = []
            except Exception:
                answer = answer_str
                picture = []

        return {
            "thought": thought,
            "answer": answer,
            "picture": picture
        }

    @staticmethod
    def is_final_answer(text: str) -> bool:
        """
        判断是否包含最终答案
        """
        if "Final Answer" in text:
            return True
        try:
            json.loads(text)
            return True
        except json.JSONDecodeError:
            return False
