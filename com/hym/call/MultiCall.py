from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from com.hym.client.AgentClient import AgentClient
from com.hym.tools.GoogleSearchTool import search
from com.hym.tools.WeatherTool import get_weather


class ExpertInput(BaseModel):
    """专家工具的统一输入：一句自然语言问题"""
    question: str = Field(description="要交给该专家处理的用户问题")


model = AgentClient().model

# ① 每个专家就是一个 create_agent（你已经有现成的天气和搜索工具）
weather_agent = create_agent(model, tools=[get_weather],
                             system_prompt="你是天气专家，只回答天气相关问题。")
search_agent = create_agent(model, tools=[search],
                            system_prompt="你是搜索专家，只负责联网检索事实信息。")


def agent_as_tool(agent: CompiledStateGraph, name: str, description: str):
    """把一个 Agent 包装成普通工具：收一句自然语言，返回最终回答"""

    @tool(name_or_callable=name, description=description)
    def _expert(question: str) -> str:
        result = agent.invoke({"messages": [HumanMessage(content=question)]})
        return result["messages"][-1].content

    return _expert


weather_expert = agent_as_tool(
    weather_agent,
    name="weather_expert",
    description="查询指定城市的实时天气、温度、风力。输入自然语言问题。",
)
search_expert = agent_as_tool(
    search_agent,
    name="search_expert",
    description="联网搜索任何实时信息、新闻、知识。输入自然语言问题。",
)

# ② 主管：自己不带工具，只做"点名"——把专家当工具调
supervisor = create_agent(
    model,
    tools=[weather_expert, search_expert],
    system_prompt=(
        "你是任务主管。分析用户请求，把子任务分派给合适的专家工具获取真实信息，"
        "再基于专家返回的结果汇总回答。涉及实时信息时必须调用专家，"
        "禁止声称自己无法查询。"
    ),
)
result = supervisor.invoke({"messages": [HumanMessage(content="北京今天适合爬山吗？")]})
print(result["messages"][-1].content)
