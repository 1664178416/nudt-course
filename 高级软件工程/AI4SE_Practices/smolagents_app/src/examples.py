"""
多智能体框架演示示例

封装了主逻辑，支持 CLI 和 Gradio UI 模式。
"""
import sys
import os

# 确保可以导入项目模块
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, PROJECT_ROOT)




def main():
    """主函数：根据命令行参数选择运行模式"""
    if "--gradio" in sys.argv or os.getenv("SMOLAGENTS_MODE") == "gradio":
        from src.apps.gradio_app import launch_gradio_demo
        launch_gradio_demo()
    else:
        from src.apps.cli_app import run_cli_example
        # 可以通过命令行传递目标，例如：python examples.py "创建一个计算器"
        goal = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
        run_cli_example(goal=goal)


if __name__ == "__main__":
    main()
