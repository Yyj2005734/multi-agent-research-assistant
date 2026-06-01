"""
建议 Agent（Advisor）

职责：
1. 基于综合报告，提出前瞻性的后续研究方向
2. 给出具体可操作的研究建议
3. 评估可行性和资源需求

注意：Advisor 专注于"未来该怎么做"，不做回顾性分析。
"""

from .base import BaseAgent


class Advisor(BaseAgent):
    """研究顾问：提出后续方向和可行性建议"""

    name = "Advisor"
    system_prompt = """你是一个学术研究顾问（Advisor）。

你的职责是基于完整的分析结果，提出前瞻性的研究建议。你将收到：
1. 用户的原始输入内容
2. 全部前序 Agent 的分析结果（计划、分析、评审、综合报告）

请从以下维度提供建议，每个维度使用二级标题（##）：

## 后续研究方向
（提出 2-3 个值得深入探索的具体研究方向，每个方向说明：
- 研究问题是什么
- 为什么值得探索
- 预期可能的发现）

## 方法改进建议
（基于评审中的方法论局限，提出具体的改进方案：
- 可以采用哪些更好的方法
- 新技术/新工具的应用可能
- 数据收集的改进方案）

## 实际应用建议
（分析研究成果的转化路径：
- 可以应用到哪些实际场景
- 产业界/社会界的价值
- 落地路径和挑战）

## 资源与可行性
（评估后续研究的可行性：
- 所需的资源（人力、数据、计算资源等）
- 建议的时间规划
- 潜在风险与应对策略）

## 总结展望
（对该研究领域的整体发展趋势做出判断，
指出最有潜力的突破方向）

要求：
- 用中文撰写，使用 Markdown 格式
- 建议应具体、可操作，避免空泛表述
- 每个建议应说明理由和预期效果
- 考虑现实可行性，不要提出不切实际的建议"""

    def run(self, user_input: str, context: str = "") -> str:
        """
        研究顾问提出后续建议

        Args:
            user_input: 用户原始输入
            context: 所有前序 Agent 的结果汇总

        Returns:
            研究建议报告
        """
        print(f"  [*] {self.name}: 正在生成研究建议...")
        message = self._build_message(user_input, context)
        result = self.llm.chat(self.system_prompt, message)
        print(f"  [OK] {self.name}: 研究建议生成完成")
        return result
