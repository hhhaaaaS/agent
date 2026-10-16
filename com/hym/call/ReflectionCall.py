from com.hym.agents.ReflectionAgent import ReflectionAgent
from com.hym.client.AgentClient import AgentClient

llm = AgentClient()

agent = ReflectionAgent(llm_client=llm)

agent.run("请实现一个快速排序算法")
