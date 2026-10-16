import os
from dataclasses import dataclass
from typing import Dict, List

from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI


@dataclass
class Context:
    system_prompt: str = "你是一个助手"


class MyState(AgentState):
    user_id: str
    call_count: int


@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    return request.runtime.context.system_prompt


# 加载环境配置
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model = os.getenv("MODEL_NAME", "glm-4-flash")


class AgentClient:

    def __init__(self, tools=None, middleware=None, debug: bool = False):
        self.model = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.5,
            timeout=300,
            max_tokens=25000,
        )
        self.client = create_agent(
            model=self.model,
            tools=tools or [],
            middleware=[dynamic_system_prompt, *(middleware or [])],
            context_schema=Context,
            state_schema=MyState,
            debug=debug
        )

    def generate(self, prompt: str, system_prompt: str) -> str:
        """调用大模型"""
        print("开始调用大模型")
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            result = self.client.invoke(
                {"messages": messages},
                context=Context(system_prompt=system_prompt)
            )
            print(f"模型返回结果：{result}")
            return result["messages"][-1].content
        except Exception as e:
            print(f"调用出错：{e}")
            return "错误:调用大语言模型服务时出错。"

    def think(self, messages: List[Dict[str, str]], temperature: float = 0, tools: list | None = None) -> str:

        """
        调用大语言模型进行思考，并返回其响应。
        """
        print("开始调用大模型(流式)")

        try:
            # bind 按次覆盖温度，不影响 self.model 的默认值
            bound = self.model
            if tools:
                bound = bound.bind_tools(tools)  # ← 模型感知工具
            bound = bound.bind(temperature=temperature)
            pieces = []
            for chunk in bound.stream(messages):
                if chunk.content:  # 跳过空 chunk（工具调用帧）
                    print(chunk.content, end="", flush=True)  # 实时逐 token 打印
                    pieces.append(chunk.content)
            print()  # 收尾换行
            return "".join(pieces)
        except Exception as e:
            print(f"\n调用出错：{e}")
            return "错误:调用大语言模型服务时出错。"

    def invoke(self, messages, temperature: float | None = None) -> AIMessage:
        """
        裸模型非流式调用：接收 LangChain 消息对象列表，返回完整 AIMessage。
        适合节点内部消费（解析结构/传给下一节点），不适合直接给用户看流式。
        """
        print("开始调用大模型")
        bound = self.model.bind(temperature=temperature) if temperature is not None else self.model
        return bound.invoke(messages)
