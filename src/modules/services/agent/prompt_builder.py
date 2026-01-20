import json
import datetime
from typing import List, Dict, Any

class PromptBuilder:
    def __init__(self, prompt_template: str, tools_description: str, tools_names: List[str]):
        self.prompt_template = prompt_template
        self.tools_description = tools_description
        self.tools_names = tools_names

    def build(self, query: str, history: List[Dict[str, Any]], context: List[Dict[str, Any]], include_system_prompt: bool = True) -> List[Dict[str, str]]:
        """
        构建发送给 LLM 的消息列表
        :param query: 当前用户问题
        :param history: 历史对话记录 (OpenAI format list of dicts)
        :param context: 当前 Agent 执行过程中的中间状态，期待每个元素包含 "raw" 字段
        :param include_system_prompt: 是否包含 System Prompt
        """
        messages = []
        
        # 1. System Prompt
        system_content = self._format_template()
        if include_system_prompt:
            messages.append({"role": "system", "content": system_content})
        
        # 2. History
        # 原逻辑: history += self.__load_history()
        messages.extend(history)
        
        # 3. Current Context
        # 原逻辑: contexts = [idx.get("raw") for idx in self.__context]
        context_raw_strs = [item.get("raw") for item in context if item and item.get("raw")]
        
        # 拼接 context
        # 原逻辑: contexts_str = self.__query + "\n" + "\n".join(json.dumps(c, ensure_ascii=False) for c in contexts if c is not None)
        # 注意: 原逻辑中 context保存的是raw string吗？
        # Check parser: raw = text (thought + action).
        # Check __close_thought_action: raw = old_raw + "\nObservation: " + observation
        # So raw is a string.
        # But wait, original code did: json.dumps(c, ensure_ascii=False) where c is from contexts list of raw strings?
        # If c is a string, json.dumps(c) will quote it. "Thought: ...".
        # Let's double check state.py logic.
        
        context_str = query + "\n" + "\n".join(json.dumps(c, ensure_ascii=False) for c in context_raw_strs)
        
        # Append Reminder
        final_user_content = (
            system_content
            + """
            Begin!

            Question: 
            """ 
            + context_str
        )
        
        messages.append({
            "role": "user",
            "content": final_user_content
        })
        
        return messages

    def _format_template(self) -> str:
        return self.prompt_template.format(
            str_tool_description=self.tools_description,
            date=str(datetime.datetime.now()),
            tool_names=", ".join(self.tools_names)
        )
