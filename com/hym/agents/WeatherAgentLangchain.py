from langchain.agents.middleware import ModelCallLimitMiddleware

from com.hym.client.AgentClient import AgentClient
from com.hym.tools.WeatherTool import get_weather

# 初始化模型客户端
llm = AgentClient(
    tools=[get_weather],
    middleware=[ModelCallLimitMiddleware(run_limit=5)],
    debug=True
)

answer = llm.generate(
    "你好，请帮我查询一下今天宜州的天气",
    system_prompt="你是天气查询助手，必须通过工具查询实时天气，禁止编造。",
)

print(answer)
