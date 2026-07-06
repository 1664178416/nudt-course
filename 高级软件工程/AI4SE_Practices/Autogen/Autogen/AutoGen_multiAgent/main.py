from llm import LLMClient
from agent import Agent
from multi_agent_system import MultiAgentSystem

def main():
    llm = LLMClient(model="gpt-4o-mini")

    researcher = Agent(
        name="Researcher",
        system_prompt="你是一名科研助理，负责分析问题并提出思路。",
        llm_client=llm
    )

    engineer = Agent(
        name="Engineer",
        system_prompt="你是一名工程师，负责把想法转化为实现方案。",
        llm_client=llm
    )

    critic = Agent(
        name="Critic",
        system_prompt="你是一名严格的评审，负责指出不足。",
        llm_client=llm
    )

    system = MultiAgentSystem({
        "Researcher": researcher,
        "Engineer": engineer,
        "Critic": critic
    })

    task = "如何加速扩散模型的采样过程？"

    system.dialogue(
        order=["Researcher", "Engineer", "Critic"],
        init_message=task
    )

if __name__ == "__main__":
    main()
