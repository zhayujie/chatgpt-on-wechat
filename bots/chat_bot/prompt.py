
PREFIX = """You are a helpful assistant.

PLUGINS:
------

Assistant has access to the following tools:"""

FORMAT_INSTRUCTIONS = """To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
{ai_prefix}: the response to the original input question in chinese
```"""

SUFFIX = """Begin!

Previous conversation history:
{chat_history}

New input: {input}
{bot_scratchpad}"""
