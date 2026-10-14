from dataclasses import dataclass

from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import dynamic_prompt, ModelRequest
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


class AgentClient:

    def __init__(self, model: str, api_key: str, base_url: str, tools=None, middleware=None, debug: bool = False):
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
