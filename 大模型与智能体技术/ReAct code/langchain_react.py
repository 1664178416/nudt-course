import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# --- 新版核心组件导入 ---
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# 注意：AgentExecutor 已被 LangGraph 取代
# 现在的 create_react_agent 来自 langgraph.prebuilt，它利用了模型原生的 Tool Calling
from langgraph.prebuilt import create_react_agent

# --- 1. 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 2. 定义工具 (保持不变，装饰器写法是通用的) ---
@tool
def search_web(query: str) -> str:
    """搜索工具，用于查询实时信息（如金价）。"""
    logger.info(f"🔎 正在调用搜索工具: {query}")
    
    # 模拟数据
    search_data = {
        "黄金": "根据最新市场数据，今日黄金价格约为 600 元/克（24K金），投资金条价格约为 580 元/克。", # 我稍微更新了一下价格使其更合理
        "gold": "Current gold price is approximately $85 per gram."
    }
    
    query_lower = query.lower()
    for key, value in search_data.items():
        if key in query_lower:
            return value
    return f"未找到关于'{query}'的信息。"

@tool
def calculate(expression: str) -> str:
    """计算工具，用于执行数学运算。"""
    logger.info(f"🧮 正在调用计算工具: {expression}")
    try:
        # 安全性过滤
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            return "错误：包含非法字符"
        return f"计算结果：{eval(expression)}"
    except Exception as e:
        return f"计算错误：{str(e)}"

# --- 3. 初始化模型 ---
# 必须使用支持 Tool Calling 的模型 (如 gpt-3.5-turbo, gpt-4o, qwen-turbo 等)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0  # 工具调用建议温度设为 0
)

# --- 4. 构建新版 Agent (LangGraph) ---
tools = [search_web, calculate]

# 核心变化：
# 1. 不再需要拉取 "hwchase17/react" 这种文本 Prompt。
# 2. create_react_agent 现在会构建一个状态图 (StateGraph)。
# 3. 它自动通过 llm.bind_tools() 将工具绑定给模型。
agent_graph = create_react_agent(model=llm, tools=tools)

# --- 5. 运行 Agent ---
def run_agent(question: str):
    print(f"\n🤖 用户提问: {question}")
    print("-" * 50)
    
    # LangGraph 的输入通常是一个消息列表
    inputs = {"messages": [HumanMessage(content=question)]}
    
    # stream=True 可以看到中间步骤，这里我们用 invoke 直接拿结果
    # config={"recursion_limit": 10} 防止死循环
    result = agent_graph.invoke(inputs)
    
    # --- 6. 解析结果 ---
    # result["messages"] 包含了完整的对话历史：
    # [用户消息, AI想调用工具的消息, 工具返回的消息, AI的最终回答]
    
    messages = result["messages"]
    
    # 打印最后一条消息（即 AI 的最终回答）
    last_message = messages[-1]
    print(f"\n💡 最终回答:\n{last_message.content}")

    # (可选) 打印中间的工具调用过程调试
    # print("\n--- 调试：执行轨迹 ---")
    # for msg in messages:
    #     print(f"[{msg.type}]: {str(msg.content)[:50]}...")

if __name__ == "__main__":
    # 测试问题
    question = "我手上有1万块钱，按今天的价格大概能买多少克黄金？"
    run_agent(question)