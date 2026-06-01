"""
命令行入口（CLI）

用法：
  python main.py                    # 交互模式（循环输入）
  python main.py "你的研究问题"       # 单次模式
  python main.py --test             # 测试 API 连接
"""

import sys
import os

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.api_client import LLMClient
from pipeline import Pipeline


def print_banner():
    """打印程序横幅"""
    print()
    print("╔════════════════════════════════════════════════╗")
    print("║       多 Agent 协作研究助手                     ║")
    print("║  Multi-Agent Collaborative Research Assistant  ║")
    print("╚════════════════════════════════════════════════╝")
    print()
    print("  Agent 角色:")
    print("    🎯 Coordinator  - 任务分解与调度")
    print("    🔍 Analyzer     - 深度内容分析")
    print("    📝 Reviewer     - 批判性评审")
    print("    🔗 Synthesizer  - 综合整合")
    print("    💡 Advisor      - 研究建议")
    print()


def print_results(results: dict):
    """格式化输出分析结果"""
    labels = {
        "plan": ("🎯 协调者 - 分析计划", "coordinator"),
        "analysis": ("🔍 分析专员 - 内容分析", "analyzer"),
        "review": ("📝 评审专员 - 批判性评审", "reviewer"),
        "synthesis": ("🔗 综合专员 - 综合报告", "synthesizer"),
        "advice": ("💡 研究顾问 - 研究建议", "advisor"),
    }

    for key, (title, _) in labels.items():
        if results.get(key):
            print(f"\n{'─' * 50}")
            print(f"  {title}")
            print(f"{'─' * 50}")
            print(results[key])
            print()

    # 耗时统计
    if results.get("steps"):
        print(f"\n{'─' * 50}")
        print("  ⏱ 耗时统计")
        print(f"{'─' * 50}")
        agent_names = {
            "coordinator": "协调者",
            "analyzer": "分析专员",
            "reviewer": "评审专员",
            "synthesizer": "综合专员",
            "advisor": "研究顾问",
        }
        for agent, t in results["steps"].items():
            name = agent_names.get(agent, agent)
            if t >= 0:
                print(f"  {name}: {t}s")
            else:
                print(f"  {name}: 失败")
        print(f"  总计: {results.get('elapsed', 0)}s")


def interactive_mode(pipeline: Pipeline):
    """交互模式：循环输入分析"""
    print("进入交互模式（输入 'quit' 或 'exit' 退出）")
    print("─" * 50)

    while True:
        print()
        user_input = input("📝 请输入研究内容（多行输入以空行结束，输入 quit 退出）:\n\n")

        if user_input.strip().lower() in ("quit", "exit", "q"):
            print("👋 再见！")
            break

        if not user_input.strip():
            print("⚠ 输入为空，请重新输入")
            continue

        # 收集多行输入
        lines = [user_input]
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)

        full_input = "\n".join(lines)

        try:
            results = pipeline.run(full_input)
            print_results(results)
        except KeyboardInterrupt:
            print("\n⚠ 分析已中断")
        except Exception as e:
            print(f"\n❌ 分析失败: {e}")


def single_mode(pipeline: Pipeline, user_input: str):
    """单次模式：分析一次后退出"""
    try:
        results = pipeline.run(user_input)
        print_results(results)
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")


def test_connection():
    """测试 API 连接"""
    print("正在测试 API 连接...")
    try:
        client = LLMClient()
        result = client.test_connection()
        if result["success"]:
            print(f"✅ 连接成功！模型: {result['model']}")
        else:
            print(f"❌ 连接失败: {result['message']}")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")


def main():
    """CLI 主入口"""
    print_banner()

    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            test_connection()
            return

        # 单次模式：直接使用命令行参数作为输入
        user_input = " ".join(sys.argv[1:])
        try:
            client = LLMClient()
            pipeline = Pipeline(client)
            single_mode(pipeline, user_input)
        except ValueError as e:
            print(f"❌ 配置错误: {e}")
            print("💡 请检查 .env 文件中的 OPENAI_API_KEY 配置")
        return

    # 交互模式
    try:
        client = LLMClient()
        pipeline = Pipeline(client)
        interactive_mode(pipeline)
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("💡 请按以下步骤配置：")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 在 .env 中填入你的 OPENAI_API_KEY")
    except KeyboardInterrupt:
        print("\n👋 再见！")


if __name__ == "__main__":
    main()
