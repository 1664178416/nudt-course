"""
ReAct实现 - 通过理解原理去实现，更好的理解ReAct的思想
"""

import logging
import re
import os
from dotenv import load_dotenv
load_dotenv()

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


DEBUG_REACT = True  # 是否输出完整 Thought（实验阶段使用）


def openai_tongyi_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model="gpt-4o-mini",
        temperature=0.2  # 降低随机性，增强可复现性
    )


# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    SEARCH = "search_web"
    CALCULATE = "calculate"
    ANSWER = "answer"
    UNKNOWN = "unknown"


@dataclass
class ReActStep:
    thought: str
    action: str
    action_type: ActionType
    action_input: str
    observation: str
    final_answer: Optional[str] = None


class ToolExecutor:
    """工具执行器：只负责确定性行为"""

    def __init__(self):
        self._tool_map = {
            ActionType.SEARCH: self._search_web,
            ActionType.CALCULATE: self._calculate
        }

    def _search_web(self, query: str) -> str:
        logger.info(f"[Tool] search_web -> {query}")

        mock_data = {
            "黄金": "【模拟数据】黄金价格约为 1159 元/克（24K，用于 ReAct 实验）",
            "gold": "【Mock Data】Gold price ~ 65 USD / gram (experiment only)"
        }

        for key, value in mock_data.items():
            if key.lower() in query.lower():
                return f"[search_web] {value}"

        return f"[search_web] 未命中模拟数据：{query}"

    def _calculate(self, expression: str) -> str:
        logger.info(f"[Tool] calculate -> {expression}")

        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "[calculate] 非法表达式"

        try:
            result = eval(expression)
            return f"[calculate] {result}"
        except Exception as e:
            return f"[calculate] 计算失败：{str(e)}"

    def execute(self, action_type: ActionType, action_input: str) -> str:
        tool_fn = self._tool_map.get(action_type)
        if not tool_fn:
            return "[system] 未知工具类型"
        return tool_fn(action_input)


class ReActParser:
    """ReAct 输出解析器（偏保守解析）"""

    ACTION_PATTERN = re.compile(r"^(\w+)\((.*)\)$")

    @staticmethod
    def parse(content: str) -> Dict[str, Any]:
        result = {
            "thought": "",
            "action": "",
            "action_type": ActionType.UNKNOWN,
            "action_input": "",
            "final_answer": None
        }

        thought_match = re.search(
            r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        action_match = re.search(
            r"Action:\s*(.*)",
            content,
            re.IGNORECASE
        )
        if action_match:
            action_text = action_match.group(1).strip()
            result["action"] = action_text

            m = ReActParser.ACTION_PATTERN.match(action_text)
            if m:
                name, param = m.groups()
                param = param.strip('"\'')
                result["action_input"] = param

                if name == "search_web":
                    result["action_type"] = ActionType.SEARCH
                elif name == "calculate":
                    result["action_type"] = ActionType.CALCULATE
                elif name == "answer":
                    result["action_type"] = ActionType.ANSWER

        final_match = re.search(
            r"Final Answer:\s*(.*)",
            content,
            re.DOTALL | re.IGNORECASE
        )
        if final_match:
            result["final_answer"] = final_match.group(1).strip()

        return result


class ReActAgent:
    """ReAct Agent 主体"""

    def __init__(self, llm, max_iterations: int = 5):
        self.llm = llm
        self.max_iterations = max_iterations
        self.executor = ToolExecutor()
        self.parser = ReActParser()
        self.history: List[Dict[str, Any]] = []

        self.system_prompt = f"""
你是一个使用 ReAct 框架的理财智能体。

约束：
1. 每轮必须输出 Thought + Action，或 Final Answer
2. Action 必须严格为 tool_name(param)
3. Observation 是系统返回的客观结果
4. {"允许完整 Thought" if DEBUG_REACT else "Thought 保持简洁"}

可用工具：
- search_web(query)
- calculate(expression)
""".strip()

    def process_question(self, question: str) -> str:
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=question)
        ]

        steps: List[ReActStep] = []

        for step_idx in range(self.max_iterations):
            response = self.llm.invoke(messages)
            content = response.content
            logger.info(f"[LLM] Step {step_idx + 1}\n{content}")

            parsed = self.parser.parse(content)

            step = ReActStep(
                thought=parsed["thought"],
                action=parsed["action"],
                action_type=parsed["action_type"],
                action_input=parsed["action_input"],
                observation="",
                final_answer=parsed["final_answer"]
            )

            if step.final_answer:
                steps.append(step)
                self._save(question, steps)
                return step.final_answer

            if step.action_type == ActionType.UNKNOWN:
                messages.append(
                    HumanMessage(
                        content="Observation: Action 无法解析，请严格使用 tool_name(param)"
                    )
                )
                continue

            observation = self.executor.execute(
                step.action_type,
                step.action_input
            )
            step.observation = observation

            messages.append(AIMessage(content=content))
            messages.append(HumanMessage(content=f"Observation: {observation}"))
            steps.append(step)

        self._save(question, steps)
        return "在限定推理步数内未能收敛。"

    def _save(self, question: str, steps: List[ReActStep]) -> None:
        self.history.append({
            "question": question,
            "steps": [step.__dict__ for step in steps]
        })


def main():
    llm = openai_tongyi_chat_model()
    agent = ReActAgent(llm)

    question = "我手上有1万块钱，我能买多少克黄金？"
    print("用户问题：", question)
    print("-" * 40)

    answer = agent.process_question(question)
    print("最终答案：", answer)


if __name__ == "__main__":
    main()
