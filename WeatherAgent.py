import json

import openai

from openai import OpenAI

# 不传参数，SDK 自动读取环境变量
client = OpenAI()

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

def get_weather(city:str,date:str="today")->dict:
    """
        查询指定城市的天气

        Args:
            city: 城市名称，如 "北京"、"上海"
            date: 日期，"today"、"tomorrow" 或 "YYYY-MM-DD" 格式

        Returns:
            包含天气信息的字典
        """
    # 模拟天气数据（实际项目调用天气 API）
    weather_data = {
        "北京": {"today": ("晴", 25), "tomorrow": ("多云", 23)},
        "上海": {"today": ("小雨", 28), "tomorrow": ("阴", 27)},
        "广州": {"today": ("雷阵雨", 31), "tomorrow": ("晴", 33)},
    }

    if date == "today":
        date_key = "today"
    elif date == "tomorrow":
        date_key = "tomorrow"
    else:
        # 如果是具体日期，简化为 today
        date_key = "today"

    if city not in weather_data:
        return {"error": f"暂不支持查询 {city} 的天气"}

    weather, temp = weather_data[city][date_key]

    return {
        "city": city,
        "date": date,
        "weather": weather,
        "temperature": f"{temp}°C",
    }

import json
from openai import OpenAI

client = OpenAI()


def run_agent(user_message: str) -> str:
    """运行 Agent：感知→决策→行动→观察"""
    messages = [
        {"role": "system", "content": "你是一个天气助手，帮用户查询天气。用自然语言回答。"},
        {"role": "user", "content": user_message},
    ]

    while True:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=messages,
            tools=tools_schema
        )

        msg = response.choices[0].message

        # 没有工具调用 → 直接返回文字
        if not msg.tool_calls:
            return msg.content

        # 把 AI 的消息加入历史
        messages.append(msg)

        # 执行工具
        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"🔧 调用工具: {func_name}({func_args})")

            if func_name == "get_weather":
                result = get_weather(**func_args)
            else:
                result = {"error": f"未知工具: {func_name}"}

            # 把工具结果加入历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })


print(run_agent("广州今天天气怎么样？"))