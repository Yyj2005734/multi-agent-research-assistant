"""
Agent 协作管线（Pipeline）

管理 5 个 Agent 的协作流程：
  Coordinator → Analyzer → Reviewer → Synthesizer → Advisor

每个 Agent 接收前序 Agent 的输出作为上下文，形成协作链。
支持流式回调（用于实时展示每个 Agent 的输出）。
"""

import time
from typing import Callable, Optional

from utils.api_client import LLMClient
from agents import Coordinator, Analyzer, Reviewer, Synthesizer, Advisor


class Pipeline:
    """
    多 Agent 协作管线

    管理 Agent 的初始化、执行顺序、上下文传递和结果收集。
    """

    # Agent 执行顺序（不可变）
    STEPS = ["coordinator", "analyzer", "reviewer", "synthesizer", "advisor"]

    def __init__(self, llm_client: LLMClient):
        """
        初始化管线，创建所有 Agent 实例

        Args:
            llm_client: LLM API 客户端
        """
        self.llm = llm_client
        self.agents = {
            "coordinator": Coordinator(llm_client),
            "analyzer": Analyzer(llm_client),
            "reviewer": Reviewer(llm_client),
            "synthesizer": Synthesizer(llm_client),
            "advisor": Advisor(llm_client),
        }

    def run(
        self,
        user_input: str,
        on_step: Optional[Callable[[str, str, str], None]] = None,
    ) -> dict:
        """
        执行完整的 Agent 协作流程

        Args:
            user_input: 用户的自然语言输入
            on_step: 步骤回调函数，签名为 (agent_name, status, result)
                     status 为 "start" 或 "done"

        Returns:
            dict: {
                "plan": str,           # Coordinator 的分析计划
                "analysis": str,       # Analyzer 的分析报告
                "review": str,         # Reviewer 的评审报告
                "synthesis": str,      # Synthesizer 的综合报告
                "advice": str,         # Advisor 的研究建议
                "elapsed": float,      # 总耗时（秒）
                "steps": dict,         # 每步耗时
            }
        """
        start_time = time.time()
        step_times = {}
        context_parts = []  # 累积上下文
        results = {}

        print("=" * 50)
        print("  多 Agent 协作分析开始")
        print("=" * 50)

        for step_name in self.STEPS:
            agent = self.agents[step_name]
            step_start = time.time()

            # 通知回调：步骤开始
            if on_step:
                on_step(step_name, "start", "")

            print(f"\n>> [{self.STEPS.index(step_name)+1}/5] {agent.name} 开始工作")

            try:
                # 构建上下文：前序所有 Agent 的结果
                context = "\n\n---\n\n".join(context_parts) if context_parts else ""

                # 执行 Agent
                result = agent.run(user_input, context)

                # 记录结果
                results[step_name] = result
                context_parts.append(f"【{agent.name}】\n{result}")

                step_time = time.time() - step_start
                step_times[step_name] = round(step_time, 2)

                # 通知回调：步骤完成
                if on_step:
                    on_step(step_name, "done", result)

                print(f"  [TIME] {agent.name} 耗时: {step_time:.1f}s")

            except Exception as e:
                error_msg = f"{agent.name} 执行失败: {e}"
                print(f"  ❌ {error_msg}")
                results[step_name] = f"执行失败: {e}"
                step_times[step_name] = -1

                if on_step:
                    on_step(step_name, "error", str(e))

        total_time = time.time() - start_time

        print(f"\n{'=' * 50}")
        print(f"  分析完成！总耗时: {total_time:.1f}s")
        print(f"{'=' * 50}")

        return {
            "plan": results.get("coordinator", ""),
            "analysis": results.get("analyzer", ""),
            "review": results.get("reviewer", ""),
            "synthesis": results.get("synthesizer", ""),
            "advice": results.get("advisor", ""),
            "elapsed": round(total_time, 2),
            "steps": step_times,
        }

    def run_stream(self, user_input: str):
        """
        流式执行：逐个 Agent 执行，yield 每个步骤的结果

        用于 CLI 实时输出或 SSE 推送给前端。

        Yields:
            dict: {
                "agent": str,      # Agent 名称
                "status": str,     # "start" | "done"
                "result": str,     # 该 Agent 的输出（status=done 时）
                "step_index": int, # 步骤序号（0-4）
            }
        """
        context_parts = []
        results = {}

        for idx, step_name in enumerate(self.STEPS):
            agent = self.agents[step_name]

            # yield: 步骤开始
            yield {
                "agent": step_name,
                "status": "start",
                "result": "",
                "step_index": idx,
            }

            # 构建上下文并执行
            context = "\n\n---\n\n".join(context_parts) if context_parts else ""

            try:
                result = agent.run(user_input, context)
                results[step_name] = result
                context_parts.append(f"【{agent.name}】\n{result}")

                # yield: 步骤完成
                yield {
                    "agent": step_name,
                    "status": "done",
                    "result": result,
                    "step_index": idx,
                }

            except Exception as e:
                yield {
                    "agent": step_name,
                    "status": "error",
                    "result": str(e),
                    "step_index": idx,
                }
