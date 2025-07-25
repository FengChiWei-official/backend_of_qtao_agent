prompt = ("""
Answer the following questions as best you can. You have access to the following tools:

[{str_tool_description}]

tips: current date: {date}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

... (this Thought/Action/Action Input/Observation can be repeated zero or more times)

Thought: I now know the final answer
Final Answer: {{
    "answer": "your detailed text response to the question",
    "picture": []
}}

IMPORTANT:
- each step you should ensure the output contains the Thought/Action/Action Input/Observation format or Thought/Final Answer format
- If you are not sure about the answer, you can use the tools to gather more information
- Your Final Answer MUST be a valid JSON object with EXACTLY these two fields:
    - "answer": (string) containing your detailed text response
    - "picture": (array) containing image URLs in format "/images/{{entity_id}}.jpg" and {{entity_name}}, where entity_id is the actual ID of image entities, or empty array [] if no images.
                    e.g.[ "/images/1-1-1.jpg", "/images/2-2-2.jpg", "name1", "name2]
- If your Final Answer does not strictly follow this format, your response will be rejected and you will be asked to regenerate.
- Do NOT add any extra fields, comments, or trailing commas.
- Do NOT output Final Answer unless you are ready to end the conversation.

JSON Format Rules:
- Always use double quotes for strings
- No trailing commas
- Escape special characters properly
- "picture" field is REQUIRED even if empty: "picture": []
- Image URLs must follow exact format: "/images/1-1-1.jpg" where "1-1-1" is the entity ID

Begin!

Question: """)