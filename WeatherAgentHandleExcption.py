import json
import time
import logging
import PlanTrip
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather_agent")


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
    },
    {
        "type": "function",
        "function": {
            "name": "plan_trip",
            "description": "根据城市和天气情况规划出行建议，需要天气信息作为输入",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "目的地城市，如 北京、上海、广州"
                    },
                    "weather_condition": {
                        "type": "string",
                        "description": "天气状况，如 晴、多云、小雨、雷阵雨"
                    },
                    "days": {
                        "type": "integer",
                        "description": "出行天数，默认1天",
                        "default": 1
                    }
                },
                "required": ["city"]
            }
        }
    }
]


def get_weather(city: str, date: str = "today") -> dict:
    """带模拟异常的天气查询"""
    weather_data = {
        "北京": {"today": ("晴", 25), "tomorrow": ("多云", 23)},
        "上海": {"today": ("小雨", 28), "tomorrow": ("阴", 27)},
        "广州": {"today": ("雷阵雨", 31), "tomorrow": ("晴", 33)},
    }

    # 模拟：不支持的城市 → 参数错误
    if city not in weather_data:
        return {
            "error": f"不支持查询 {city} 的天气，目前支持：北京、上海、广州",
            "supported_cities": list(weather_data.keys()),
        }

    # 模拟：随机超时（20%概率）
    import random
    if random.random() < 0.2:
        raise TimeoutError("天气服务响应超时，请稍后重试")

    weather, temp = weather_data[city].get(date, weather_data[city]["today"])
    return {
        "city": city,
        "date": date,
        "weather": weather,
        "temperature": f"{temp}°C",
    }

def execute_tool_with_retry(func_name: str, func_args: dict, max_retries: int = 3) -> dict:
    """
    执行工具，带指数退避重试

    Args:
        func_name: 工具名
        func_args: 工具参数
        max_retries: 最大重试次数

    Returns:
        工具结果字典（成功或错误信息）
    """
    for attempt in range(max_retries + 1):
        try:
            if func_name == "get_weather":
                result = get_weather(**func_args)
            elif func_name =="plan_trip" :
                result = PlanTrip.plan_trip(**func_args)
            else:
                result = {"error": f"未知工具: {func_name}"}
            return result

        except TimeoutError as e:
            if attempt < max_retries:
                # 指数退避：1s → 2s → 4s
                wait_time = 2 ** attempt
                logger.warning(f"⚠️ 第 {attempt+1} 次重试，等待 {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ 超过最大重试次数 ({max_retries})")
                return {
                    "error": f"天气服务暂时不可用，已重试 {max_retries} 次。建议稍后再试。",
                    "retry_attempts": max_retries,
                }

        except json.JSONDecodeError as e:
            # 不可重试的错误 → 直接降级
            logger.error(f"❌ 参数解析失败（不可重试）: {e}")
            return {
                "error": f"参数格式错误，无法解析: {str(e)}",
                "raw_args": str(func_args),
            }

        except TypeError as e:
            # 参数类型错误 → 不可重试，告诉 AI
            logger.error(f"❌ 参数类型错误（不可重试）: {e}")
            return {
                "error": f"工具参数错误: {str(e)}",
                "expected_params": "city (str), date (str, optional)",
            }

        except Exception as e:
            # 未知异常 → 降级，不暴露内部细节
            logger.error(f"❌ 未知异常: {type(e).__name__}: {e}")
            return {
                "error": "工具执行遇到未知错误，请稍后再试或换个方式提问。",
            }

def run_agent_robust(user_message: str) -> str:
    """带异常处理的 Agent"""
    messages = [
        {"role": "system", "content": "你是一个天气助手。如果工具返回错误信息，请根据错误提示调整策略或如实告诉用户。"},
        {"role": "user", "content": user_message},
    ]

    while True:
        try:
            response = client.chat.completions.create(
                model="glm-4-flash",
                messages=messages,
                tools=tools_schema,
            )
        except Exception as e:
            # LLM API 本身出错
            logger.error(f"❌ LLM API 异常: {e}")
            return "抱歉，AI 服务暂时不可用，请稍后再试。"

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        messages.append(msg)

        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                # AI 返回了无效 JSON → 直接告诉 AI
                func_args = {}
                logger.warning(f"⚠️ AI 返回无效参数")

            print(f"🔧 调用工具: {func_name}({func_args})")

            # 使用带重试的工具执行
            result = execute_tool_with_retry(func_name, func_args)

            print(f"📦 结果: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

def run_multi_tool_agent(user_message: str) -> str:
    """多工具协作 Agent"""
    messages = [
        {
            "role": "system",
            "content": "你是一个出行助手，可以查询天气和规划行程。\n"
                       "如果用户问出行建议，先查天气再规划行程。\n"
                       "如果工具返回错误，根据错误信息调整策略。",
        },
        {"role": "user", "content": user_message},
    ]

    tool_map = {
        "get_weather": get_weather,
        "plan_trip": PlanTrip.plan_trip,
    }

    while True:
        try:
            response = client.chat.completions.create(
                model="glm-4-flash",
                messages=messages,
                tools=tools_schema,
            )
        except Exception as e:
            return f"AI 服务暂时不可用: {e}"

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        messages.append(msg)

        for tool_call in msg.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            print(f"🔧 调用: {func_name}({func_args})")

            # 使用带重试的执行（复用 2.8 节的代码）
            result = execute_tool_with_retry(func_name, func_args)

            print(f"📦 结果: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

# 测试多工具协作
print("=== 简单天气查询 ===")
print(run_multi_tool_agent("北京明天天气怎么样？"))

print("\n=== 出行建议（触发双工具协作） ===")
print(run_multi_tool_agent("北京明天适不适合出游？"))

print("\n=== 直接问行程（Agent 自行决定先查天气） ===")
print(run_multi_tool_agent("帮我规划一下上海的行程"))

