import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents.middleware import ModelCallLimitMiddleware

from com.hym.tools.WeatherTool import get_weather

from com.hym.client.AgentClient import AgentClient

# 加载环境配置
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / "env" / "AgentConfig.env")  # ← 显式路径
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model = os.getenv("MODEL_NAME", "glm-4-flash")

# 初始化模型客户端
llm = AgentClient(
    model=model,
    api_key=api_key,
    base_url=base_url,
    tools=[get_weather],
    middleware=[ModelCallLimitMiddleware(run_limit=5)],
    debug=True
)

answer = llm.generate(
    "你好，请帮我查询一下今天北京的天气",
    system_prompt="你是天气查询助手，必须通过工具查询实时天气，禁止编造。",
)

print(answer)
