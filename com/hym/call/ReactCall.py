from com.hym.agents.SearchAgent import ReActAgent
from com.hym.client.AgentClient import AgentClient
from com.hym.tools.GoogleSearchTool import search

llm = AgentClient()

# 工具注册表：模型输出的 Action 名 → 实际执行的 Python 函数
available_tools = {
    "search": search,  # 注意：函数对象，不带括号
}

agent = ReActAgent(
    llm_client=llm,
    available_tools=available_tools
)

agent.react_run("什么动物会汪汪叫？")
