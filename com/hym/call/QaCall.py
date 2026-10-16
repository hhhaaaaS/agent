from langchain_core.messages import HumanMessage

from com.hym.agents.QaAssistantAgent import QaAssistantAgent
from com.hym.client.AgentClient import AgentClient
from com.hym.tools.GoogleSearchTool import search

llm = AgentClient()
agent = QaAssistantAgent(llm_client=llm, search_tool=search)
app = agent.create_search_assistant()
# ── 启动调用 ──
result = app.invoke(
    {"messages": [HumanMessage(content="什么是阿卡夏记录？")]},  # 初始 State：只需要给 messages
    config={"configurable": {"thread_id": "qa-demo-1"}},  # checkpointer 必需
)

print(result["final_answer"])
