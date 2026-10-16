from typing import TypedDict, Annotated

from langgraph.graph import add_messages


class SearchState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str  # 经过LLM理解后的用户需求总结
    search_query: str  # 优化后用于 SerpApi API的搜索查询
    search_results: str  # SerpApi搜索返回的结果
    final_answer: str  # 最终生成的答案
    step: str  # 标记当前步骤