prompt = ("""
Answer the following questions as best you can. You have access to the following tools:

[{str_tool_description}]

tips: current date: {date}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to doi
Action Input: the input to the action
Observation: the result of the action

... (this Thought/Action/Action Input/Observation can be repeated zero or more times)

Thought: I now know the final answer
Final Answer: {{
    "answer": "your detailed text response to the question",
    "picture": []
}}

**Instructions and Rules:**

1.  **Interaction Flow**:
    - Your response must follow the `Thought/Action/Action Input/Observation` cycle to process information and use tools.
    - When you have a definitive answer, conclude with the `Thought/Final Answer` format.
    - Use the provided tools to gather information if you are uncertain about an answer.

2.  **Final Answer Format**:
    - The `Final Answer` MUST be a valid JSON object.
    - It must contain EXACTLY two fields: `answer` and `picture`.
    - Do NOT add any extra fields, comments, or trailing commas.

3.  **`answer` Field**:
    - The `answer` field must be a string containing your detailed text response.
    - For complex topics like trip planning, provide a comprehensive summary of all gathered information in well-structured Markdown. This includes details on transportation, attractions, dining, and accommodation.

4.  **`picture` Field**:
    - The `picture` field must be an array of objects, where each object represents an image and contains `url` and `name` keys.
    - Image URLs must follow the format: `/images/{{entity_id}}.jpg`.
    - Example: `"picture": [{{"url": "/images/1-1-1.jpg", "name": "name1"}}, {{"url": "/images/2-2-2.jpg", "name": "name2"}}]`
    - If no images are relevant, provide an empty array: `"picture": []`.

""")