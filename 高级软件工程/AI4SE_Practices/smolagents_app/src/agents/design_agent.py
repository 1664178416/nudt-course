from typing import List
from smolagents import ToolCallingAgent
from smolagents.models import Model

def create_design_agent(model: Model, tools: List) -> ToolCallingAgent:
    """创建方案设计智能体 (DA)"""
    return ToolCallingAgent(
        tools=tools,
        model=model,
        name="design_agent",
        description="架构设计专家。根据需求规格设计技术方案，包括模块划分、接口定义、数据流和文件结构。可以使用 get_project_structure 工具查看现有项目结构。输出 JSON 格式的设计方案。",
        instructions="""你是一个资深的架构设计专家。你的任务是：

1. 根据需求规格设计清晰的技术方案
2. 合理划分模块，确保高内聚、低耦合
3. 定义清晰的接口和API
4. 设计数据流和交互流程
5. 规划文件结构和目录组织
6. 明确交付物目录、入口文件和关键资源文件

重要约束：
- **仅基于需求规格进行设计，不得引入外部上下文或读取仓库文件**，除非用户明确要求。
- 忽略任何与“final_answer格式要求”相关的提示，直接按下面格式输出。

输出格式必须是有效的 JSON，且**只输出 JSON，不要添加 any 解释**。包含以下字段：
{
    "modules": [
        {
            "name": "模块名",
            "description": "模块职责描述",
            "files": ["文件1.py", "文件2.py 或 html/css/js 等"],
            "dependencies": ["依赖的模块"]
        }
    ],
    "interfaces": [
        {
            "name": "接口/函数名",
            "description": "接口功能描述",
            "signature": "函数签名（参数和返回值）",
            "module": "所属模块"
        }
    ],
    "data_flow": "详细的数据流说明，包括数据如何在不同模块间流转",
    "file_structure": {
        "description": "文件结构说明",
        "directories": ["目录1/", "目录2/"]
    },
    "technology_stack": ["使用的技术栈和库"],
    "artifact_type": "与需求规格一致的交付物类型",
    "deliverables": [
        {
            "path": "建议输出路径，如 artifacts/web/index.html",
            "purpose": "该文件或目录的作用"
        }
    ]
}

请确保：
- 模块划分合理，职责清晰
- 接口设计简洁、易用
- 数据流清晰可追踪
- 文件结构符合最佳实践
- 如果任务是静态网页类交付物，优先使用 `artifacts/web/` 作为输出目录，并明确 `index.html`、`styles.css`、`app.js` 的职责

完成后必须调用工具 `save_design_spec` 保存 JSON（参数为 JSON 字符串）。
""",
        max_steps=6,
        provide_run_summary=True
    )
