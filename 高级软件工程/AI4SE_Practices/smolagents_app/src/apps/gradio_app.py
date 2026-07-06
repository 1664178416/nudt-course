"""
Gradio UI 启动入口
"""

from ..runtime.run_context import create_run_dir, run_context, set_global_run_dir
from ..utils import save_results_to_output
from ..parsing.output_parser import parse_agent_output
from ..task_profiles import build_execution_brief, save_task_profile
from ..fallback_runner import run_fallback_static_web_task


def _attach_run_context(agent):
    """
    尽量保留 smolagents 原生 Agent 类型，只包裹 run 行为，
    这样 GradioUI 还能使用它自己的中间过程展示能力。
    """

    original_run = agent.run

    def wrapped_run(*args, **kwargs):
        run_dir = create_run_dir()
        set_global_run_dir(run_dir)
        print(f"[INFO] 任务输出目录: {run_dir}")

        task_text = args[0] if args else ""
        (run_dir / "input").mkdir(parents=True, exist_ok=True)
        with open(run_dir / "input" / "task.txt", "w", encoding="utf-8") as f:
            f.write(task_text)

        save_task_profile(task_text, run_dir)
        enriched_task = build_execution_brief(task_text, run_dir)

        with run_context(run_dir):
            try:
                result = original_run(enriched_task, **kwargs)
            except Exception as exc:
                message = str(exc)
                if "Error while parsing tool call" in message or "JSON blob" in message:
                    print("[WARN] 检测到工具调用解析失败，切换到极速兜底流程。")
                    fallback_result = run_fallback_static_web_task(
                        task_text,
                        run_dir,
                        logger=lambda msg: print(f"[FAST] {msg}"),
                    )
                    return fallback_result["ui_message"]
                raise

            if hasattr(result, "output"):
                output = result.output
            else:
                output = str(result)

            parsed = parse_agent_output(output)
            save_results_to_output(
                requirement_spec=parsed.get("requirement_spec"),
                design_spec=parsed.get("design_spec"),
                implementation=parsed.get("implementation") or {"output": output},
                verification_report=parsed.get("verification_report"),
                task_goal=task_text,
            )
            return result

    agent.run = wrapped_run
    return agent


def launch_gradio_demo() -> None:
    """启动多智能体框架 Gradio UI"""
    try:
        from smolagents import GradioUI
        from ..factories.model_factory import create_model
        from ..factories.manager_factory import create_manager_agent
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "当前环境缺少 smolagents 或其 UI 依赖，无法启动 Gradio 模式。"
        ) from exc

    model = create_model()
    manager_agent = create_manager_agent(model, save_results=True)
    manager_agent = _attach_run_context(manager_agent)

    print("启动多智能体框架 Gradio UI...")
    print("=" * 60)
    print("[TIP] Gradio 模式优先保留 smolagents 原生中间过程展示。")
    print("[TIP] 若工具调用解析失败，会自动切换到极速兜底流程并输出可读过程。")
    print("=" * 60)

    demo = GradioUI(manager_agent)
    demo.launch()
