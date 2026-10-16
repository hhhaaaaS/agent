import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv(Path("env/AgentConfig.env"))

from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """查询城市实时天气"""
    return "晴 21度"

class Dump(BaseCallbackHandler):
    def on_chat_model_start(self, serialized, messages, **kwargs):
        print("=== 本次发给 LLM 的消息 ===")
        for msg in messages[0]:
            c = msg.content
            print(f"role={getattr(msg, 'type', '?')} | content类型={type(c).__name__} | {str(c)[:80]}")

llm = ChatOpenAI(model="glm-4-flash", api_key=os.getenv("API_KEY"),
                base_url=os.getenv("BASE_URL"), temperature=0)
weather_agent = create_agent(llm, tools=[get_weather], system_prompt="你是天气专家")

class ExpertInput(BaseModel):
    question: str = Field(description="问题")

t = weather_agent.as_tool(name="weather_expert", description="查天气",
                          args_schema=ExpertInput)

print("直接调用包装工具:")
try:
    r = t.invoke({"question": "北京今天天气如何"}, config={"callbacks": [Dump()]})
    print("工具返回:", str(r)[:100])
except Exception as e:
    print("失败:", str(e)[:150])
