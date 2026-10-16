from typing import TypedDict, List


# 定义全局状态的数据结构
class AgentState(TypedDict):
    messages: List[str]  # 对话历史
    current_task: str  # 当前任务
    final_answer: str  # 最终答案
