from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from com.hym.client.AgentClient import AgentClient
from com.hym.memory.state.AgentState import AgentState
from com.hym.memory.state.SearchState import SearchState


class QaAssistantAgent:

    def __init__(self, llm_client: AgentClient, search_tool: BaseTool):

        self.llm_client = llm_client
        self.search_tool = search_tool

    def understand_query_node(self, state: SearchState) -> dict:
        """步骤1：理解用户查询并生成搜索关键词"""
        user_message = state["messages"][-1].content

        understand_prompt = f"""分析用户的查询："{user_message}"
    请完成两个任务：
    1. 简洁总结用户想要了解什么
    2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

    格式：
    理解：[用户需求总结]
    搜索词：[最佳搜索关键词]"""

        response = self.llm_client.invoke(
            [SystemMessage(content=understand_prompt), HumanMessage(content=user_message)])
        response_text = response.content

        # 解析LLM的输出，提取搜索关键词
        search_query = user_message  # 默认使用原始查询
        if "搜索词：" in response_text:
            search_query = response_text.split("搜索词：")[1].strip()

        return {
            "user_query": response_text,
            "search_query": search_query,
            "step": "understood",
            "messages": [AIMessage(content=f"我将为您搜索：{search_query}")]
        }

    def google_search_node(self, state: SearchState) -> dict:
        """步骤2：调用注入的搜索工具"""
        search_query = state["search_query"]
        try:
            print(f"🔎 正在搜索: {search_query}")
            # BaseTool 的标准调用：参数名必须和工具签名对上（query）
            search_results = self.search_tool.invoke({"query": search_query})

            return {
                "search_results": str(search_results),
                "step": "searched",
                "messages": [AIMessage(content="搜索完成！正在整理答案...")]
            }
        except Exception as e:
            return {
                "search_results": f"搜索失败：{e}",
                "step": "search_failed",
                "messages": [AIMessage(content="搜索遇到问题...")]
            }

    def generate_answer_node(self, state: SearchState) -> dict:
        """步骤3：基于搜索结果生成最终答案"""
        if state["step"] == "search_failed":
            # 如果搜索失败，执行回退策略，基于LLM自身知识回答
            fallback_prompt = f"搜索API暂时不可用，请基于您的知识回答用户的问题：\n用户问题：{state['user_query']}"
            response = self.llm_client.invoke(
                [SystemMessage(content=fallback_prompt), HumanMessage(content=state["user_query"])])
        else:
            # 搜索成功，基于搜索结果生成答案
            answer_prompt = f"""基于以下搜索结果为用户提供完整、准确的答案：
    用户问题：{state['user_query']}
    搜索结果：\n{state['search_results']}
    请综合搜索结果，提供准确、有用的回答..."""
            response = self.llm_client.invoke(
                [SystemMessage(content=answer_prompt), HumanMessage(content=state["user_query"])])

        return {
            "final_answer": response.content,
            "step": "completed",
            "messages": [AIMessage(content=response.content)]
        }

    def should_continue(self, state: AgentState) -> str:
        """条件函数：根据状态决定下一步路由。"""
        # 假设如果消息少于3条，则需要继续规划
        if len(state["messages"]) < 3:
            # 返回的字符串需要与添加条件边时定义的键匹配
            return "continue_to_planner"
        else:
            state["final_answer"] = state["messages"][-1]
            return "end_workflow"

    # 定义一个“规划者”节点函数
    def planner_node(self, state: AgentState) -> AgentState:
        """根据当前任务制定计划，并更新状态。"""
        current_task = state["current_task"]
        # ... 调用LLM生成计划 ...
        plan = f"为任务 '{current_task}' 生成的计划..."

        # 将新消息追加到状态中
        state["messages"].append(plan)
        return state

    # 定义一个“执行者”节点函数
    def executor_node(self, state: AgentState) -> AgentState:
        """执行最新计划，并更新状态。"""
        latest_plan = state["messages"][-1]
        # ... 执行计划并获得结果 ...
        result = f"执行计划 '{latest_plan}' 的结果..."

        state["messages"].append(result)
        return state

    def create_search_assistant(self):
        workflow = StateGraph(SearchState)

        # 添加节点
        workflow.add_node("understand", self.understand_query_node)
        workflow.add_node("search", self.google_search_node)
        workflow.add_node("answer", self.generate_answer_node)

        # 设置线性流程
        workflow.add_edge(START, "understand")
        workflow.add_edge("understand", "search")
        workflow.add_edge("search", "answer")
        workflow.add_edge("answer", END)

        # 编译图
        memory = InMemorySaver()
        app = workflow.compile(checkpointer=memory)
        return app
