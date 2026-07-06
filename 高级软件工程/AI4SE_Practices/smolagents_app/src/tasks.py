"""
Task 数据结构

定义 Task 配置和示例 Task（如"生成页面骨架"、"代码审查"等）。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Task:
	"""任务配置"""
	name: str
	goal: str
	context_paths: List[str] = field(default_factory=list)
	constraints: Dict[str, str] = field(default_factory=dict)
	description: Optional[str] = None


class TaskRegistry:
	"""任务注册表"""

	def __init__(self):
		self._tasks: Dict[str, Task] = {}

	def register(self, task: Task) -> None:
		self._tasks[task.name] = task

	def get(self, name: str) -> Optional[Task]:
		return self._tasks.get(name)

	def list(self) -> List[Task]:
		return list(self._tasks.values())


def build_default_registry() -> TaskRegistry:
	"""构建默认任务集合"""
	registry = TaskRegistry()

	registry.register(
		Task(
			name="calculator",
			description="基础功能：生成一个带测试与README的计算器程序",
			goal="创建一个简单的计算器程序，支持加减乘除四则运算，包含单元测试和 README 文档",
		)
	)
	registry.register(
		Task(
			name="code_review",
			description="代码审查：分析现有仓库并给出改进建议",
			goal="对当前仓库进行代码质量审查，输出主要问题清单与改进建议",
		)
	)
	registry.register(
		Task(
			name="test_generation",
			description="测试生成：为现有模块补充单元测试",
			goal="为当前项目中核心模块生成单元测试，并说明如何运行",
		)
	)
	registry.register(
		Task(
			name="doc_update",
			description="文档完善：补充或更新 README 与使用说明",
			goal="为当前项目补充/更新 README，包含安装、运行与示例说明",
		)
	)
	registry.register(
		Task(
			name="algorithm_showcase_web",
			description="前端演示：生成一个好看的算法展示网页并输出到 output 运行目录",
			goal="做一个好看的前端网页，展示各种算法，放到 /output目录下",
		)
	)

	return registry

