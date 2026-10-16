
import json
import re
from typing import Callable, Any

from langchain_core.tools import BaseTool

from com.hym.client.AgentClient import AgentClient

react_system_prompt = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `tool_name[tool_input]`:调用一个可用工具。
- `Finish[最终答案]`:当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action:字段后使用 Finish[最终答案] 来输出最终答案。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""


class ReActAgent:

    def __init__(self, llm_client: AgentClient, available_tools: dict[str, Callable[..., Any]], max_steps: int = 5):
        self.llm_client = llm_client
        self.available_tools = available_tools
        self.max_steps = max_steps
        self.history = []

    def react_run(self, question: str):
        """
        运行ReAct智能体来回答一个问题。
        """

        self.history = []  # 每次运行时重置历史记录
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"--- 第 {current_step} 步 ---")

            # 1. 格式化提示词
            tools_desc = self.available_tools
            history_str = "\n".join(self.history)
            prompt = react_system_prompt.format(
                tools=tools_desc,
                question=question,
                history=history_str
            )

            # 2. 调用LLM进行思考
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)

            if not response_text:
                print("错误:LLM未能返回有效响应。")
                break
            else:
                self.history.append(response_text)

            # 3. 解析LLM的输出
            thought, action = self._parse_output(response_text)

            if thought:
                print(f"思考: {thought}")

            if not action:
                print("警告:未能解析出有效的Action，流程终止。")
                break

            # 4. 执行Action
            if action.startswith("Finish"):
                # 如果是Finish指令，提取最终答案并结束
                final_answer = re.match(r"Finish\[(.*)\]", action).group(1)
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            print(tool_name, tool_input)
            if not tool_name or not tool_input:
                # ... 处理无效Action格式 ...
                continue

            print(f"🎬 行动: {tool_name}[{tool_input}]")

            tool_function = self.available_tools.get(tool_name)
            if tool_function is None:
                self.history.append(
                    f"Observation: 错误:未找到工具'{tool_name}'，可用: {list(self.available_tools)}"
                )
                continue

            try:
                if isinstance(tool_function, BaseTool):
                    # tool_input 是 JSON 字符串或纯文本 → 统一转成参数 dict
                    try:
                        args = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
                    except json.JSONDecodeError:
                        first_param = next(iter(tool_function.args), None)  # 纯文本 → 映射首参数
                        args = {first_param: tool_input}
                    observation = tool_function.invoke(args)
                else:
                    observation = tool_function(tool_input)  # 普通函数才用括号
            except Exception as e:
                observation = f"错误:工具执行失败 - {e}"

            print(f"👀 Observation: {str(observation)[:200]}")
            self.history.append(f"Observation: {observation}")

    def _parse_output(self, text: str):
        """解析LLM的输出，提取Thought和Action。
        """
        # Thought: 匹配到 Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """解析Action字符串，提取工具名称和输入。
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None
