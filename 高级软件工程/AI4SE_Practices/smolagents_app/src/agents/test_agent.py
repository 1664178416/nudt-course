from typing import List
from smolagents import CodeAgent
from smolagents.models import Model

def create_test_agent(model: Model, tools: List) -> CodeAgent:
    """创建测试智能体 (TA)"""
    return CodeAgent(
        tools=tools,
        model=model,
        name="test_agent",
        description="测试专家。根据需求与设计生成测试代码，仅写入 tests/ 目录。",
        instructions="""你是一个严格的测试工程师。你的任务是：

    1. 根据需求规格与设计方案生成测试用例
    2. 测试应覆盖核心功能与边界条件
    3. 根据交付物类型选择合适的测试策略
    4. 只生成测试代码，不修改任何源码

    工具使用：
    - write_test_file: 将测试文件写入 tests/ 目录

    硬性要求：
    - **必须至少生成 1 个测试文件**，文件名建议 tests/test_basic.py 或 tests/test_calculator.py
    - **必须调用 write_test_file 至少一次**，禁止仅口头描述
    - 所有测试文件必须写入 tests/ 子目录
    - 仅生成测试代码

    测试策略提示：
    - 若任务是 Python 应用或 API 服务，生成可直接运行的单元测试
    - 若任务是静态网页或前端展示页，生成 smoke test，至少检查入口文件、资源引用、关键 DOM 结构或关键文本

    输出：只生成测试代码内容并写入文件，不输出路径说明或解释文字。
    """,
        max_steps=6,
        provide_run_summary=True
    )
