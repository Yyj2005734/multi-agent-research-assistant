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
    system_prompt = """你是学术研究顾问（Advisor）。基于分析结果提出前瞻性研究建议。

维度（每项用 ## 标题）：
## 后续研究方向：2-3个具体方向，说明问题、价值、预期发现
## 方法改进建议：更好方法、新技术应用、数据改进
## 实际应用建议：应用场景、产业价值、落地路径
## 资源与可行性：所需资源、时间规划、风险应对
## 总结展望：领域趋势、突破方向

要求：用中文，Markdown格式，建议具体可操作，说明理由和预期效果，考虑现实可行性。"""

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
