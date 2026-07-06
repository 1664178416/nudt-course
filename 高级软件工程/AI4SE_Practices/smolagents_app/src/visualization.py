"""
多智能体协作流程可视化工具
支持生成Mermaid流程图、时序图，导出为HTML/PNG
"""
import json
from typing import Dict, List, Optional
from pathlib import Path

from .monitoring import global_monitor, AgentExecutionMetrics
from .orchestrator import RunResult
from .data.specs import RequirementSpec, DesignSpec, VerificationReport


class AgentFlowVisualizer:
    """智能体流程可视化生成器"""

    def __init__(self, run_dir: Optional[str] = None):
        self.run_dir = run_dir or "runs/default"
        self.metrics: List[AgentExecutionMetrics] = []
        self.load_metrics()

    def load_metrics(self):
        """从运行目录加载监控指标"""
        metrics_file = Path(f"{self.run_dir}/agent_metrics.json")
        if metrics_file.exists():
            with open(metrics_file, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)
                self.metrics = [
                    AgentExecutionMetrics(
                        agent_type=m["agent_type"],
                        agent_id=m["agent_id"],
                        task_id=m["task_id"],
                        start_time=m["start_time"],
                        end_time=m["end_time"],
                        duration=m["duration"],
                        status=m["status"],
                        error_msg=m["error_msg"],
                        output_size=m["output_size"]
                    ) for m in metrics_data
                ]

    def generate_mermaid_flow(self) -> str:
        """生成Mermaid流程图"""
        # 按执行时间排序
        sorted_metrics = sorted(self.metrics, key=lambda x: x.start_time)
        # 构建节点和连线
        nodes = []
        edges = []
        prev_agent = None

        for idx, m in enumerate(sorted_metrics):
            status_style = "style fill:#f0f0f0" if m.status == "success" else "style fill:#ffeeee"
            node_id = f"{m.agent_type}_{idx}"
            nodes.append(f"{node_id}[{m.agent_type} (Task: {m.task_id[:8]})] {status_style}")

            if prev_agent:
                edges.append(f"{prev_agent} --> {node_id}")
            prev_agent = node_id

        # 拼接Mermaid语法
        mermaid = f"""
flowchart TD
    {"\n    ".join(nodes)}
    {"\n    ".join(edges)}
    classDef success fill:#f0f0f0
    classDef failed fill:#ffeeee
"""
        return mermaid

    def generate_mermaid_sequence(self) -> str:
        """生成Mermaid时序图"""
        sorted_metrics = sorted(self.metrics, key=lambda x: x.start_time)
        steps = []
        for m in sorted_metrics:
            steps.append(f"    {m.agent_type}->>Orchestrator: Execute Task {m.task_id[:8]}")
            steps.append(
                f"    note over {m.agent_type}: Status: {m.status}\n    note over {m.agent_type}: Duration: {m.duration:.2f}s")

        mermaid = f"""
sequenceDiagram
    participant Orchestrator
    participant RA as RequirementAgent
    participant DA as DesignAgent
    participant IA as ImplementationAgent
    participant VA as VerificationAgent
    {"\n    ".join(steps)}
"""
        return mermaid

    def export_to_html(self, output_path: str = "agent_flow.html"):
        """导出可视化结果到HTML"""
        flow_mermaid = self.generate_mermaid_flow()
        sequence_mermaid = self.generate_mermaid_sequence()

        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>多智能体协作流程可视化</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        .mermaid-container {{
            margin: 20px;
            padding: 20px;
            border: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <h1>多智能体协作流程图</h1>
    <div class="mermaid-container">
        {flow_mermaid}
    </div>
    <h1>多智能体执行时序图</h1>
    <div class="mermaid-container">
        {sequence_mermaid}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"可视化HTML已导出至: {output_path}")


# 便捷函数：快速生成当前运行的可视化报告
def generate_flow_visualization(run_dir: Optional[str] = None):
    """生成智能体流程可视化报告"""
    visualizer = AgentFlowVisualizer(run_dir)
    visualizer.export_to_html()
    return visualizer