from pathlib import Path

p = Path("com/hym/agents/QaAssistantAgent.py")
t = p.read_text(encoding="utf-8")
orig = t

# 1. 补 import
t = t.replace(
    "from langchain_core.messages import SystemMessage, AIMessage",
    "from langchain_core.messages import SystemMessage, HumanMessage, AIMessage",
    1,
)

# 2. understand 节点
t = t.replace(
    "self.llm_client.invoke([SystemMessage(content=understand_prompt)])",
    'self.llm_client.invoke([SystemMessage(content=understand_prompt), HumanMessage(content=user_message)])',
    1,
)

# 3. answer 节点-回退分支
t = t.replace(
    "self.llm_client.invoke([SystemMessage(content=fallback_prompt)])",
    'self.llm_client.invoke([SystemMessage(content=fallback_prompt), HumanMessage(content=state["user_query"])])',
    1,
)

# 4. answer 节点-正常分支
t = t.replace(
    "self.llm_client.invoke([SystemMessage(content=answer_prompt)])",
    'self.llm_client.invoke([SystemMessage(content=answer_prompt), HumanMessage(content=state["user_query"])])',
    1,
)

# 校验四处都改到了
checks = [
    "HumanMessage, AIMessage",
    "HumanMessage(content=user_message)",
    'HumanMessage(content=state["user_query"])',
]
for c in checks:
    print(c, "->", t.count(c), "处")

p.write_text(t, encoding="utf-8")
print("写入完成" if t != orig else "没有变化（模式未匹配！）")
