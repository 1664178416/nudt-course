"""
CLI 示例入口：运行任务并保存结果
"""

import json
from ..runtime.run_context import create_run_dir, run_context, set_global_run_dir
from ..tasks import build_default_registry
from ..utils import save_results_to_output
from ..parsing.output_parser import parse_agent_output
from ..task_profiles import build_execution_brief, build_task_profile, save_task_profile
from ..fallback_runner import run_fallback_static_web_task
from ..execution_mode import should_use_fast_path


def run_cli_example(goal: str | None = None, task_name: str | None = None):
    """命令行示例：不使用 Gradio UI，支持结果保存"""
    registry = build_default_registry()
    selected_goal = goal

    if task_name:
        task = registry.get(task_name)
        if task:
            selected_goal = task.goal
        else:
            print(f"[WARN] 未找到任务: {task_name}，将使用自定义目标")

    if not selected_goal:
        tasks = registry.list()
        print("可用任务:")
        for task in tasks:
            desc = f" - {task.name}: {task.description}" if task.description else f" - {task.name}"
            print(desc)
        selected_goal = tasks[0].goal if tasks else "请描述你的任务目标"

    run_dir = create_run_dir()
    set_global_run_dir(run_dir)

    print("=" * 60)
    print("多智能体框架演示")
    print("=" * 60)
    print(f"任务目标: {selected_goal}\n")

    print("--- 开始多智能体协作 ---\n")
    print(f"[INFO] 任务输出目录: {run_dir}")
    (run_dir / "input").mkdir(parents=True, exist_ok=True)
    with open(run_dir / "input" / "task.txt", "w", encoding="utf-8") as f:
        f.write(selected_goal)
    profile_path = save_task_profile(selected_goal, run_dir)
    enriched_goal = build_execution_brief(selected_goal, run_dir)
    print(f"[INFO] 任务画像已保存: {profile_path}")

    if should_use_fast_path(selected_goal):
        print("[INFO] 已启用极速模式：静态网页任务将走简化流程（更快、更稳）。")
        with run_context(run_dir):
            result = run_fallback_static_web_task(selected_goal, run_dir)
        print("[OK] 极速模式执行完成。")
        return result

    try:
        from ..factories.model_factory import create_model
        from ..factories.manager_factory import create_manager_agent

        model = create_model()
        manager_agent = create_manager_agent(model, save_results=True)

        with run_context(run_dir):
            result = manager_agent.run(enriched_goal, return_full_result=True)
    except ModuleNotFoundError as exc:
        profile = build_task_profile(selected_goal)
        if profile.artifact_type == "static_web_app":
            print(f"[WARN] 检测到缺少运行依赖，将切换到本地静态网页降级模式: {exc}")
            with run_context(run_dir):
                fallback_result = run_fallback_static_web_task(selected_goal, run_dir)
            print("[OK] 已通过本地降级模式生成前端交付物。")
            return fallback_result
        raise
    except Exception as exc:
        profile = build_task_profile(selected_goal)
        if profile.artifact_type == "static_web_app":
            message = str(exc)
            if "Error while parsing tool call" in message or "JSON blob" in message:
                print("[WARN] 检测到工具调用解析失败，自动切换极速模式以保证任务完成。")
                with run_context(run_dir):
                    fallback_result = run_fallback_static_web_task(selected_goal, run_dir)
                print("[OK] 已通过极速模式完成网页交付。")
                return fallback_result
        raise

    if hasattr(result, 'output'):
        output = result.output
    else:
        output = str(result)
    parsed = parse_agent_output(output)

    print("\n" + "=" * 60)
    print("保存结果到 output/ 目录...")
    print("=" * 60)

    with run_context(run_dir):
        saved_files = save_results_to_output(
            requirement_spec=parsed.get("requirement_spec"),
            design_spec=parsed.get("design_spec"),
            implementation=parsed.get("implementation") or {"output": output},
            verification_report=parsed.get("verification_report"),
            task_goal=selected_goal,
        )
        if parsed.get("verification_report"):
            try:
                verification = json.loads(parsed["verification_report"])
                print(f"[INFO] 验证状态: {'通过' if verification.get('passed') else '未通过'}")
            except Exception:
                pass

    print("\n[OK] 结果已保存：")
    for key, path in saved_files.items():
        print(f"  - {key}: {path}")

    print("\n" + "=" * 60)
    print("执行结果")
    print("=" * 60)
    print(output[:500] + "..." if len(output) > 500 else output)
    print("=" * 60)

    return result
