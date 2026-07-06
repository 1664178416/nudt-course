"""
智能体执行监控与日志分析工具
"""
import time
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from .runtime import get_current_run_dir, run_context
from .agents import (
    RequirementAgent,
    DesignAgent,
    ImplementationAgent,
    VerificationAgent,
)

# 配置监控日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(agent_type)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_monitor.log"),
        logging.StreamHandler()
    ]
)

@dataclass
class AgentExecutionMetrics:
    """智能体执行指标"""
    agent_type: str  # RA/DA/IA/VA
    agent_id: str
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # 执行时长（秒）
    status: str = "running"  # running/success/failed
    error_msg: Optional[str] = None
    output_size: Optional[int] = None  # 输出内容大小（字节）

class AgentMonitor:
    """智能体监控器"""
    def __init__(self):
        self.metrics_store: Dict[str, AgentExecutionMetrics] = {}  # key: task_id-agent_id
        self.run_dir = get_current_run_dir() or "runs/default"

    @contextmanager
    def track_agent(self, agent: Any, task_id: str):
        """上下文管理器：跟踪智能体执行"""
        agent_type = self._get_agent_type(agent)
        agent_id = id(agent)
        track_key = f"{task_id}-{agent_id}"
        
        # 初始化监控指标
        metrics = AgentExecutionMetrics(
            agent_type=agent_type,
            agent_id=str(agent_id),
            task_id=task_id,
            start_time=datetime.now()
        )
        self.metrics_store[track_key] = metrics

        try:
            # 注入监控日志到智能体上下文
            run_context.set("monitoring", {"track_key": track_key, "monitor": self})
            yield metrics
            
            # 执行成功
            metrics.end_time = datetime.now()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.status = "success"
            self._log_metrics(metrics)
        except Exception as e:
            # 执行失败
            metrics.end_time = datetime.now()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.status = "failed"
            metrics.error_msg = str(e)
            self._log_metrics(metrics, level=logging.ERROR)
            raise e
        finally:
            # 保存指标到文件
            self.save_metrics_to_file()

    def _get_agent_type(self, agent: Any) -> str:
        """识别智能体类型"""
        if isinstance(agent, RequirementAgent):
            return "RA"
        elif isinstance(agent, DesignAgent):
            return "DA"
        elif isinstance(agent, ImplementationAgent):
            return "IA"
        elif isinstance(agent, VerificationAgent):
            return "VA"
        else:
            return "UNKNOWN"

    def _log_metrics(self, metrics: AgentExecutionMetrics, level: int = logging.INFO):
        """记录监控日志"""
        extra = {"agent_type": metrics.agent_type}
        if metrics.status == "success":
            msg = (
                f"Agent {metrics.agent_id} (Task {metrics.task_id}) completed in {metrics.duration:.2f}s "
                f"(Output size: {metrics.output_size or 0} bytes)"
            )
            logging.log(level, msg, extra=extra)
        else:
            msg = (
                f"Agent {metrics.agent_id} (Task {metrics.task_id}) failed after {metrics.duration:.2f}s: "
                f"{metrics.error_msg}"
            )
            logging.log(level, msg, extra=extra)

    def save_metrics_to_file(self):
        """保存所有指标到运行目录"""
        metrics_file = f"{self.run_dir}/agent_metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(m) for m in self.metrics_store.values()],
                f,
                ensure_ascii=False,
                default=str
            )

    def get_agent_stats(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """统计智能体执行情况"""
        filtered = [m for m in self.metrics_store.values() if agent_type is None or m.agent_type == agent_type]
        if not filtered:
            return {"total": 0, "success": 0, "failed": 0, "avg_duration": 0}
        
        success = len([m for m in filtered if m.status == "success"])
        failed = len([m for m in filtered if m.status == "failed"])
        avg_duration = sum(m.duration or 0 for m in filtered) / len(filtered)
        
        return {
            "total": len(filtered),
            "success": success,
            "failed": failed,
            "success_rate": success / len(filtered) * 100,
            "avg_duration": round(avg_duration, 2)
        }

# 全局监控实例
global_monitor = AgentMonitor()

# 便捷装饰器：跟踪智能体方法执行
def track_agent_method(func):
    def wrapper(self, *args, **kwargs):
        task_id = run_context.get("task_id", "unknown")
        with global_monitor.track_agent(self, task_id) as metrics:
            result = func(self, *args, **kwargs)
            # 统计输出大小
            if result:
                metrics.output_size = len(str(result))
            return result
    return wrapper