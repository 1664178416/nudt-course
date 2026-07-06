# SmolAgents 多智能体软件工程框架

## 项目概述

本项目是一个基于 [smolagents](https://github.com/huggingface/smolagents) 开源框架改造的**多智能体软件工程自动化系统**。该系统通过多个专业化智能体的协作，实现从需求分析到代码实现、测试生成、质量验证的完整软件工程流程自动化。

### 核心价值

- **自动化软件工程流程**：将传统的"需求→设计→实现→测试→验证"流程完全自动化
- **多智能体协作**：通过专业化智能体分工，实现高质量的软件工程输出
- **可追溯、可审计**：所有输出结构化保存，便于评审、对比和二次开发
- **教学与工程双适用**：既可用于课程实验，也可用于实际工程场景

---

## 一、关注的智能化开发问题

### 1.1 软件工程流程自动化的挑战

传统软件开发流程中，从需求分析到最终交付涉及多个阶段，每个阶段都需要专业知识和大量人工参与。本框架致力于解决以下核心问题：

#### 问题 1：需求到实现的鸿沟
- **现状**：自然语言需求难以直接转化为可执行代码，中间需要大量人工分析和设计
- **解决**：通过需求分析智能体（RA）自动提取结构化需求规格，再由设计智能体（DA）生成技术方案

#### 问题 2：代码质量与测试覆盖不足
- **现状**：开发人员往往优先实现功能，测试和质量检查容易被忽视
- **解决**：强制测试智能体（TA）生成测试用例，验证智能体（VA）进行质量检查

#### 问题 3：上下文污染与噪声干扰
- **现状**：AI 代码生成工具容易读取无关文件，产生噪声输出
- **解决**：严格限制智能体只能访问任务目录，用户输入为唯一事实来源

#### 问题 4：多阶段协作的复杂性
- **现状**：不同阶段的输出需要人工传递和协调
- **解决**：通过管理智能体（Manager）统一编排，自动传递阶段输出

### 1.2 多智能体系统的设计挑战

#### 挑战 1：职责边界划分
- **解决方案**：每个智能体有明确的职责和工具权限，通过工具层实现权限隔离
- **实现**：需求智能体只能保存需求 JSON，实现智能体只能写入 src/，测试智能体只能写入 tests/

#### 挑战 2：输出格式一致性
- **解决方案**：通过结构化 JSON 规范各阶段输出，便于解析和验证
- **实现**：RequirementSpec、DesignSpec、VerificationReport 等数据模型

#### 挑战 3：任务目录隔离
- **解决方案**：每次运行创建独立的时间戳目录，避免输出污染
- **实现**：通过 `run_context` 管理任务目录，工具层强制路径校验

---

## 二、依托的开源项目

### 2.1 smolagents 简介

[smolagents](https://github.com/huggingface/smolagents) 是 HuggingFace 开发的轻量级智能体框架，具有以下特点：

- **极简设计**：核心代码仅约 1000 行，抽象层最小化
- **代码智能体优先**：支持 `CodeAgent`，智能体以 Python 代码片段形式执行动作
- **模型无关**：支持任何 LLM（OpenAI、Anthropic、本地模型等）
- **工具生态丰富**：支持 MCP 服务器、LangChain 工具、Hub Space 等
- **多模态支持**：支持文本、视觉、视频、音频输入

### 2.2 为什么选择 smolagents？

1. **轻量级架构**：代码简洁，易于理解和改造
2. **代码智能体模式**：更适合软件工程场景，智能体可以直接编写代码
3. **多智能体支持**：原生支持 `managed_agents` 模式，便于实现智能体协作
4. **活跃社区**：HuggingFace 维护，文档完善，生态丰富

### 2.3 本项目的改造点

在 smolagents 基础上，本项目进行了以下关键改造：

1. **多智能体编排**：实现 Manager Agent 协调五个专业化智能体
2. **工具权限隔离**：为不同智能体分配不同工具集，实现职责分离
3. **任务目录管理**：实现运行上下文管理，确保输出隔离
4. **结构化输出**：定义 RequirementSpec、DesignSpec 等数据模型
5. **流程自动化**：实现从需求到验证的完整自动化流程

---

## 三、总体思路

### 3.1 架构设计理念

本框架采用**三层架构**设计：

```
┌─────────────────────────────────────────┐
│  流程层（Process Layer）                │
│  Manager Agent 统一编排                 │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  智能体层（Agent Layer）                │
│  RA → DA → IA → TA → VA                 │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  工具层（Tool Layer）                   │
│  文件操作、代码分析、测试执行等         │
└─────────────────────────────────────────┘
```

#### 流程层
- **职责**：统一编排五个智能体的执行顺序
- **实现**：通过 `create_manager_agent` 创建管理智能体，使用 `managed_agents` 模式

#### 智能体层
- **需求分析智能体（RA）**：从自然语言提取结构化需求规格
- **方案设计智能体（DA）**：根据需求规格设计技术方案
- **实现智能体（IA）**：根据设计方案生成代码
- **测试智能体（TA）**：生成测试用例
- **验证智能体（VA）**：验证实现是否满足需求

#### 工具层
- **文件工具**：`read_file`、`write_source_file`、`write_test_file`
- **代码分析工具**：`analyze_code`、`check_code_quality`
- **测试工具**：`run_test`
- **规格保存工具**：`save_requirement_spec`、`save_design_spec`、`save_verification_report`

### 3.2 工作流程

```
用户输入任务
    ↓
[RA] 需求分析 → input/requirement.json
    ↓
[DA] 方案设计 → design/design.json
    ↓
[IA] 代码实现 → src/*.py
    ↓
[TA] 测试生成 → tests/test_*.py
    ↓
[VA] 质量验证 → logs/verification.json
    ↓
输出总结 → logs/summary.md
```

### 3.3 核心设计原则

#### 原则 1：用户输入为唯一事实来源
- 禁止智能体读取无关文件造成噪声
- 除非用户明确要求，否则不读取仓库其他文件

#### 原则 2：输出目录隔离
- 每次运行创建 `output/<时间戳>/` 独立目录
- 所有输出严格限制在任务目录内

#### 原则 3：职责严格分离
- 每个智能体只能使用特定工具集
- 实现智能体只能写 src/，测试智能体只能写 tests/

#### 原则 4：结构化输出
- 需求、设计、验证均以 JSON 格式输出
- 便于解析、验证和二次生成

---

## 四、目前进展

### 4.1 已实现功能

#### ✅ 核心智能体系统
- [x] **需求分析智能体（RA）**：从自然语言提取结构化需求规格
- [x] **方案设计智能体（DA）**：根据需求规格设计技术方案
- [x] **实现智能体（IA）**：使用 CodeAgent 生成代码文件
- [x] **测试智能体（TA）**：生成测试用例（强制至少生成 1 个文件）
- [x] **验证智能体（VA）**：验证实现是否满足需求

#### ✅ 管理智能体
- [x] **Manager Agent**：使用 `managed_agents` 模式协调五个智能体
- [x] **流程编排**：自动按 RA → DA → IA → TA → VA 顺序执行
- [x] **结果传递**：自动将前一阶段输出传递给下一阶段

#### ✅ 工具系统
- [x] **文件工具**：读写文件、目录操作、文件搜索
- [x] **代码分析工具**：AST 解析、代码质量检查
- [x] **测试工具**：pytest/unittest 执行
- [x] **规格保存工具**：需求、设计、验证报告的 JSON 保存

#### ✅ 运行上下文管理
- [x] **任务目录创建**：自动创建 `output/<时间戳>/` 目录
- [x] **路径隔离**：工具层强制校验，禁止访问任务目录外路径
- [x] **全局上下文**：支持跨线程/上下文访问任务目录

#### ✅ 用户界面
- [x] **CLI 模式**：命令行执行，任务完成后自动退出
- [x] **Gradio UI**：Web 界面，常驻服务，支持交互式使用

#### ✅ 结果保存
- [x] **结构化输出**：需求、设计、代码、测试、验证报告分别保存
- [x] **总结报告**：自动生成 `logs/summary.md` 执行摘要

### 4.2 项目结构

```
smolagents_app/
├── README.md                    # 项目说明文档
├── .gitignore                   # Git 忽略配置
├── src/                         # 源代码目录
│   ├── __init__.py
│   ├── agents/                  # 智能体包（RA/DA/IA/TA/VA）
│   │   ├── __init__.py
│   │   ├── requirement_agent.py
│   │   ├── design_agent.py
│   │   ├── implementation_agent.py
│   │   ├── test_agent.py
│   │   └── verification_agent.py
│   │
│   ├── tools/                   # 工具包（分模块管理）
│   │   ├── __init__.py
│   │   ├── base.py              # 基础工具与路径解析
│   │   ├── file_tools.py        # 文件操作工具
│   │   ├── code_tools.py        # 代码分析与质量检查
│   │   ├── test_tools.py        # 测试执行工具
│   │   ├── doc_tools.py         # 文档生成工具
│   │   └── spec_tools.py        # 规格保存工具
│   │
│   ├── orchestrator.py          # 任务编排器（兼容接口）
│   ├── tasks.py                 # 任务注册表与示例任务
│   ├── config.py                # 配置管理
│   ├── utils.py                 # 工具函数（结果保存、格式化等）
│   ├── examples.py              # 主入口（简洁封装）
│   │
│   ├── apps/                    # 应用入口
│   │   ├── cli_app.py           # CLI 模式入口
│   │   └── gradio_app.py        # Gradio UI 入口
│   │
│   ├── data/                    # 数据模型
│   │   └── specs.py             # 数据结构定义
│   │
│   ├── factories/               # 工厂模式
│   │   ├── model_factory.py     # 模型创建工厂
│   │   └── manager_factory.py   # 管理智能体创建工厂
│   │
│   ├── parsing/                 # 解析模块
│   │   └── output_parser.py     # 输出解析器
│   │
│   └── runtime/                 # 运行时管理
│       └── run_context.py       # 运行上下文管理
│
└── output/                      # 输出目录（时间戳隔离）
```

### 4.3 技术栈

- **智能体框架**：smolagents（HuggingFace）
- **LLM 支持**：OpenAI API、HuggingFace Inference API、本地模型
- **代码执行**：Python AST 解析、pytest/unittest 测试框架
- **用户界面**：Gradio（Web UI）、CLI（命令行）
- **数据格式**：JSON（结构化输出）、Markdown（文档）

### 4.4 典型使用示例

#### 示例 1：命令行执行

```bash
cd smolagents_app/src
python examples.py
```

或指定任务：

```python
from apps.cli_app import run_cli_example
run_cli_example(goal="创建一个简单计算器，支持加减乘除并处理除零")
```

#### 示例 2：Gradio UI

```bash
python examples.py --gradio
```

或设置环境变量：

```bash
set SMOLAGENTS_MODE=gradio
python examples.py
```

#### 示例 3：使用任务注册表

```python
from tasks import build_default_registry
registry = build_default_registry()
task = registry.get("calculator")
# 使用 task.goal 作为任务目标
```

### 4.5 输出示例

执行任务后，会在 `output/<时间戳>/` 目录下生成：

- **input/task.txt**：用户原始需求
- **input/requirement.json**：需求规格（功能列表、约束、验收标准）
- **design/design.json**：设计方案（模块划分、接口定义、数据流）
- **src/***.py**：实现代码（多个 Python 文件）
- **tests/test_*.py**：测试代码（至少 1 个测试文件）
- **logs/verification.json**：验证报告（通过/失败、问题清单、改进建议）
- **logs/summary.md**：执行摘要（生成文件列表、执行状态）

---

## 五、推进计划

### 5.1 短期计划（1-2 个月）

#### 功能完善
- [ ] **测试覆盖率提升**：增强测试智能体，支持边界测试、异常测试模板
- [ ] **代码质量检查增强**：集成 pylint、black、mypy 等工具
- [ ] **错误处理优化**：完善异常捕获和错误提示机制
- [ ] **输出格式优化**：改进 JSON 解析，支持更灵活的输出格式

#### 用户体验
- [ ] **CLI 参数支持**：支持命令行参数指定任务、模型、输出目录
- [ ] **进度显示**：添加执行进度条和阶段状态提示
- [ ] **日志系统**：完善日志记录，支持调试模式

#### 文档完善
- [ ] **API 文档**：生成完整的 API 文档
- [ ] **使用教程**：编写详细的使用教程和最佳实践
- [ ] **示例扩展**：添加更多任务示例（Web 应用、API 服务等）

### 5.2 中期计划（3-6 个月）

#### 智能体能力提升
- [ ] **需求分析增强**：支持更复杂的需求场景（多模块、分布式系统）
- [ ] **设计模式支持**：智能体能够识别和应用常见设计模式
- [ ] **代码重构能力**：实现智能体支持代码重构和优化
- [ ] **文档生成**：自动生成 API 文档、用户手册等

#### 多语言支持
- [ ] **多编程语言**：支持 JavaScript、Java、Go 等语言
- [ ] **多框架支持**：支持 React、Django、Flask 等框架

#### 集成与扩展
- [ ] **CI/CD 集成**：支持与 GitHub Actions、GitLab CI 集成
- [ ] **版本控制集成**：支持 Git 操作，自动提交代码
- [ ] **外部工具集成**：集成更多外部工具（数据库、API 测试等）

### 5.3 长期计划（6-12 个月）

#### 高级功能
- [ ] **多智能体并行**：支持部分智能体并行执行，提升效率
- [ ] **智能体学习**：支持从历史任务中学习，优化输出质量
- [ ] **需求迭代**：支持需求变更时的增量更新
- [ ] **代码审查**：实现自动代码审查和代码评审报告

#### 企业级特性
- [ ] **权限管理**：支持多用户、角色权限管理
- [ ] **任务队列**：支持任务队列和批量处理
- [ ] **监控与告警**：实现任务监控、性能分析和告警机制
- [ ] **数据持久化**：支持数据库存储任务历史和结果

#### 研究与优化
- [ ] **性能优化**：优化智能体调用效率，减少 LLM API 调用次数
- [ ] **成本控制**：实现成本估算和优化策略
- [ ] **质量评估**：建立自动化质量评估体系
- [ ] **基准测试**：建立标准测试集，持续评估系统性能

### 5.4 技术债务与重构

- [ ] **代码重构**：优化代码结构，提升可维护性
- [ ] **测试覆盖**：为框架本身添加单元测试和集成测试
- [ ] **类型注解**：完善类型注解，提升代码可读性
- [ ] **错误处理**：统一错误处理机制，提升健壮性

---

## 六、技术细节

### 6.1 智能体定义

#### 需求分析智能体（RA）

```python
def create_requirement_agent(model: Model, tools: List) -> ToolCallingAgent:
    """创建需求分析智能体"""
    return ToolCallingAgent(
        tools=tools,  # 仅包含 save_requirement_spec
        model=model,
        name="requirement_agent",
        description="需求分析专家。从自然语言需求中提取结构化需求规格。",
        instructions="...",  # 详细的提示词
        max_steps=20,
    )
```

**输出格式**：
```json
{
    "functions": ["功能1", "功能2", ...],
    "constraints": ["约束1", "约束2", ...],
    "acceptance_criteria": ["验收标准1", ...],
    "non_functional_requirements": ["非功能性需求1", ...]
}
```

#### 方案设计智能体（DA）

```python
def create_design_agent(model: Model, tools: List) -> ToolCallingAgent:
    """创建方案设计智能体"""
    return ToolCallingAgent(
        tools=tools,  # 仅包含 save_design_spec
        model=model,
        name="design_agent",
        description="架构设计专家。根据需求规格设计技术方案。",
        instructions="...",
        max_steps=20,
    )
```

**输出格式**：
```json
{
    "modules": [{"name": "...", "description": "...", "files": [...]}],
    "interfaces": [{"name": "...", "signature": "..."}],
    "data_flow": "...",
    "file_structure": {...},
    "technology_stack": [...]
}
```

#### 实现智能体（IA）

```python
def create_implementation_agent(model: Model, tools: List) -> CodeAgent:
    """创建实现智能体"""
    return CodeAgent(
        tools=tools,  # 包含 write_source_file
        model=model,
        name="implementation_agent",
        description="开发专家。根据设计方案生成高质量代码。",
        instructions="...",
        max_steps=50,
    )
```

**特点**：使用 `CodeAgent`，智能体以 Python 代码形式执行动作，更适合代码生成场景。

#### 测试智能体（TA）

```python
def create_test_agent(model: Model, tools: List) -> CodeAgent:
    """创建测试智能体"""
    return CodeAgent(
        tools=tools,  # 包含 write_test_file
        model=model,
        name="test_agent",
        description="测试专家。根据需求与设计生成测试代码。",
        instructions="...",  # 强制要求至少生成 1 个测试文件
        max_steps=30,
    )
```

#### 验证智能体（VA）

```python
def create_verification_agent(model: Model, tools: List) -> ToolCallingAgent:
    """创建验证智能体"""
    return ToolCallingAgent(
        tools=tools,  # 包含 check_code_quality、run_test、save_verification_report
        model=model,
        name="verification_agent",
        description="质量保证专家。验证实现是否满足需求。",
        instructions="...",
        max_steps=25,
    )
```

### 6.2 工具权限隔离

系统通过工具集分配实现权限隔离：

```python
def get_requirement_tools() -> List[Tool]:
    """需求分析阶段工具（只写需求 JSON）"""
    return [save_requirement_spec]

def get_implementation_tools() -> List[Tool]:
    """实现阶段工具（只写 src/）"""
    return [write_source_file]

def get_test_tools() -> List[Tool]:
    """测试阶段工具（只写 tests/）"""
    return [write_test_file]

def get_verification_tools() -> List[Tool]:
    """验证阶段工具（只读 + 检查）"""
    return [check_code_quality, run_test, save_verification_report]
```

### 6.3 运行上下文管理

```python
@contextmanager
def run_context(run_dir: Path):
    """设置当前任务运行目录上下文"""
    token = _CURRENT_RUN_DIR.set(run_dir)
    os.environ["SMOLAGENTS_RUN_DIR"] = str(run_dir)
    try:
        yield run_dir
    finally:
        _CURRENT_RUN_DIR.reset(token)
```

工具层通过 `get_current_run_dir()` 获取任务目录，并强制校验路径：

```python
def _ensure_within_run_dir(path: Path, run_dir: Path) -> Path:
    """确保路径在任务目录内"""
    resolved = path.resolve()
    run_resolved = run_dir.resolve()
    if not resolved.is_relative_to(run_resolved):
        raise RuntimeError("禁止访问任务目录之外的路径")
    return resolved
```

### 6.4 管理智能体实现

```python
def create_manager_agent(model: Model, ...) -> CodeAgent:
    """创建主智能体，管理五个子智能体"""
    requirement_agent = create_requirement_agent(...)
    design_agent = create_design_agent(...)
    implementation_agent = create_implementation_agent(...)
    test_agent = create_test_agent(...)
    verification_agent = create_verification_agent(...)

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
        instructions=DEFAULT_MANAGER_INSTRUCTIONS,
        max_steps=80,
    )
    return manager_agent
```

管理智能体通过 `managed_agents` 模式协调子智能体，按照固定流程执行。

---

## 七、使用指南

### 7.1 环境配置

#### 安装依赖

```bash
pip install smolagents
# 如果需要使用 OpenAI API
pip install openai
# 如果需要使用 Gradio UI
pip install gradio
```

#### 配置 API 密钥

```bash
# OpenAI API
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选

# 或使用 HuggingFace Inference API
# 无需配置，直接使用 InferenceClientModel
```

### 7.2 快速开始

#### 方式 1：命令行执行

```bash
cd smolagents_app/src
python examples.py
```

系统会提示选择任务或输入自定义任务目标。

#### 方式 2：Gradio UI

```bash
python examples.py --gradio
```

在浏览器中打开显示的 URL，输入任务目标，点击运行。

#### 方式 3：编程调用

```python
from src.apps.cli_app import run_cli_example

# 执行自定义任务
run_cli_example(goal="创建一个简单计算器，支持加减乘除并处理除零")

# 或使用任务注册表中的任务
run_cli_example(task_name="calculator")
```

### 7.3 自定义配置

#### 修改模型配置

编辑 `src/config.py`：

```python
@dataclass
class ModelConfig:
    provider: str = "openai"
    model_id: str = "gpt-4o-mini"  # 修改为你的模型
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
```

#### 添加自定义任务

编辑 `src/tasks.py`：

```python
registry.register(
    Task(
        name="my_task",
        description="我的自定义任务",
        goal="任务目标描述",
    )
)
```

### 7.4 输出解读

执行完成后，查看 `output/<时间戳>/` 目录：

1. **input/task.txt**：用户原始需求（最高级参考）
2. **input/requirement.json**：需求分析结果（功能列表、约束、验收标准）
3. **design/design.json**：设计方案（模块划分、接口定义）
4. **src/***.py**：实现代码（可直接运行）
5. **tests/test_*.py**：测试代码（可用 pytest 运行）
6. **logs/verification.json**：验证报告（通过/失败、问题清单）
7. **logs/summary.md**：执行摘要（生成文件列表、执行状态）

---