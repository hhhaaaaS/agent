from langchain.agents.middleware import ModelRetryMiddleware, ToolErrorMiddleware, ModelCallLimitMiddleware, \
    ToolRetryMiddleware
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市指定日期的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "date": {"type": "string", "description": "日期", "default": "today"}
                },
                "required": ["city"]
            }
        }
    }
]


@tool(description="查询指定城市指定日期的天气信息")
def getWeather(city: str, date: str = "today") -> dict:
    """当用户消息中出现任何城市名并询问天气/温度时，立即调用本工具，不要向用户确认城市。"""
    weatherData = {

        "北京": {"today": ("晴", 26.5), "tomorrow": {"阴", 25}},
        "上海": {"today": ("小雨", 28), "tomorrow": ("阴", 27)},
        "广州": {"today": ("雷阵雨", 31), "tomorrow": ("晴", 33)}
    }

    if date == "today":
        date_key = "today"
    elif date == "tomorrow":
        date_key = "tomorrow"
    else:
        # 如果是具体日期，简化为 today
        date_key = "today"

    if city not in weatherData:
        return {"error": f"暂不支持查询 {city} 的天气"}

    weather, temp = weatherData[city][date_key]

    return {
        "city": city,
        "date": date,
        "weather": weather,
        "temperature": f"{temp}°C",
    }


from langchain.agents import create_agent;

# api_key 在这里配，不在 create_agent 里
llm = ChatOpenAI(
    model="glm-4-flash",
    api_key="29e7b543d8b74041a36c8a60123e2fb3.Pfm8L1BOUQvxKLVV",
    base_url="https://open.bigmodel.cn/api/paas/v4/",  # 指定厂商
    temperature=0
)

agent = create_agent(
    llm,
    tools=[getWeather],
    middleware=[ModelRetryMiddleware(max_retries=3),
                ToolRetryMiddleware(),
                ModelCallLimitMiddleware(run_limit=10),
                ],
    checkpointer=InMemorySaver(),
    system_prompt="你是天气查询助手。只要用户消息中出现城市并询问天气或温度，"
                  "必须立即调用 getWeather 工具查询，禁止反问用户已知信息，"
                  "禁止凭记忆编造天气数据。")


def run_agent(user_message: str) -> str:
    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ]
    })
    print("AI调用结果： ")
    print(result)
    reply = result["messages"][-1].content
    return reply


def chat(user_message: str, thread_id: str = "default") -> str:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config={"configurable": {"thread_id": thread_id}},   # ← 改动 2：报身份
    )
    return result["messages"][-1].content


# ── 多轮对话演示 ──
print(chat("北京今天的天气怎么样？"))   # 第1轮：调工具，答"晴 26.5°C"
print(chat("那明天呢？"))               # 第2轮：模型记得在聊北京，自动查明天
print(chat("换成上海呢？"))             # 第3轮：切换城市，仍知道要查天气
