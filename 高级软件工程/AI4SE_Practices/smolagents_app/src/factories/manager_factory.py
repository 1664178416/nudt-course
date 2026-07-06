"""
管理智能体工厂：创建负责协调四类子智能体的 Manager Agent
"""

from smolagents import CodeAgent
from smolagents.models import Model
from ..tools import (
    get_requirement_tools,
    get_design_tools,
    get_implementation_tools,
    get_test_tools,
    get_verification_tools,
)
from ..agents import (
    create_requirement_agent,
    create_design_agent,
    create_implementation_agent,
    create_test_agent,
    create_verification_agent,
)

DEFAULT_MANAGER_INSTRUCTIONS = """
你是一个软件工程项目的管理者，负责协调多个专业团队成员完成软件开发任务：

1. **requirement_agent（需求分析专家）**
   - 职责：分析需求，提取功能列表、约束和验收标准
   - 输出：JSON 格式的需求规格

2. **design_agent（架构设计专家）**
   - 职责：根据需求规格设计技术方案，包括模块划分和接口定义
   - 输出：JSON 格式的设计方案

3. **implementation_agent（开发专家）**
   - 职责：根据设计方案生成代码，创建文件
   - 输出：生成的代码和文件

4. **test_agent（测试专家）**
    - 职责：根据需求与设计生成测试代码或 smoke test
    - 输出：tests/ 目录中的测试文件

5. **verification_agent（质量保证专家）**
   - 职责：验证实现是否满足需求，检查代码质量
   - 输出：JSON 格式的验证报告

**工作流程**：
1. 首先调用 requirement_agent 分析需求，获取需求规格
2. 然后调用 design_agent 根据需求规格设计方案
3. 接着调用 implementation_agent 根据设计方案实现代码
4. 随后调用 test_agent 生成测试代码（必须写入 tests/ 至少一个文件）
5. 最后调用 verification_agent 验证实现是否满足需求

**重要提示**：
- 每个阶段完成后，将结果传递给下一个阶段
- 确保所有阶段都完成
- 如果某个阶段发现问题，及时反馈并调整
- 最终输出应该包含完整的项目代码和文档
- **需求为唯一事实来源**，不得从仓库或文档中引入额外上下文
- 除非用户明确要求，否则不得读取任何文件
- 你必须根据 requirement_spec / design_spec 中的 artifact_type 调整后续流程
- 若 artifact_type 为静态网页，最终交付物应落在 `artifacts/web/` 等交付目录，而不是只生成 Python 源码
- 若任务要求“放到 /output 目录下”，当前任务运行目录本身就位于 output/ 下，应把最终产物写到该运行目录内部

请按照这个流程协调团队成员完成任务。

执行细则：
- 调用 test_agent 时必须传入 requirement_spec 与 design_spec 作为上下文
- 若未生成测试文件，必须重新调用 test_agent 直至写入至少一个 tests/ 文件
- 若实现的是网页类交付物，必须确认入口文件和静态资源已真正生成，再进入验证阶段
"""


def create_manager_agent(
    model: Model,
    save_results: bool = True,
    max_steps: int = 24,
    instructions: str = DEFAULT_MANAGER_INSTRUCTIONS,
) -> CodeAgent:
    """创建主智能体（Manager Agent），管理四个子智能体"""
    requirement_agent = create_requirement_agent(model, get_requirement_tools())
    design_agent = create_design_agent(model, get_design_tools())
    implementation_agent = create_implementation_agent(model, get_implementation_tools())
    test_agent = create_test_agent(model, get_test_tools())
    verification_agent = create_verification_agent(model, get_verification_tools())

    manager_agent = CodeAgent(
        tools=[],
        managed_agents=[
            requirement_agent,
            design_agent,
            implementation_agent,
            test_agent,
            verification_agent,
        ],
        model=model,
        instructions=instructions,
        max_steps=max_steps,
    )

    # 注意：结果保存逻辑在 CLI/Gradio 应用中实现
    # 这里不设置回调，因为 managed_agents 的复杂性使得回调机制难以实现

    return manager_agent
