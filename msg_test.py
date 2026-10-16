import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path("env/AgentConfig.env"))
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatOpenAI(model="glm-4-flash", api_key=os.getenv("API_KEY"),
                base_url=os.getenv("BASE_URL"), temperature=0)

print("== 测试1: 只有 SystemMessage ==")
try:
    r = llm.invoke([SystemMessage(content="你是助手")])
    print("OK:", r.content[:30])
except Exception as e:
    print("失败:", str(e)[:120])

print("== 测试2: System + Human ==")
try:
    r = llm.invoke([SystemMessage(content="你是助手"), HumanMessage(content="你好")])
    print("OK:", r.content[:30])
except Exception as e:
    print("失败:", str(e)[:120])
