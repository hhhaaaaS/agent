from com.hym.agents.PlannerAgent import PlannerAgent
from com.hym.client.AgentClient import AgentClient

llm = AgentClient()

plan = PlannerAgent(llm_client=llm)

plan.run(question="问题: 一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？")


