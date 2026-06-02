"""
评审 Agent（Reviewer）

职责：
1. 对 Analyzer 的分析结果进行批判性评审
2. 评估研究的创新性（理论/方法/应用创新）
3. 识别方法论局限性和研究不足
4. 提出改进建议

注意：Reviewer 专注于批判性评估，不做内容分析（那是 Analyzer 的职责）。
"""

from .base import BaseAgent


class Reviewer(BaseAgent):
    """评审专员：批判性评估创新性和局限性"""

    name = "Reviewer"
    system_prompt = """你是学术评审专家（Reviewer）。对研究进行批判性评审。

维度（每项用 ## 标题）：
## 创新性评估：理论/方法/应用创新，与现有研究对比
## 方法论评审：方法合理性、设计严谨性、可复现性
## 局限性分析：方法论/数据/推广性局限、未解决问题
## 改进建议：方法改进、数据补充、研究扩展

要求：用中文，Markdown格式，评审有理有据引用原文，按协调者指定的评审重点展开。"""

    def run(self, user_input: str, context: str = "") -> str:
        """
        评审专员执行批判性评审

        Args:
            user_input: 用户原始输入
            context: Coordinator 计划 + Analyzer 分析结果

        Returns:
            结构化的评审报告
        """
        print(f"  [*] {self.name}: 正在进行批判性评审...")
        message = self._build_message(user_input, context)
        result = self.llm.chat(self.system_prompt, message)
        print(f"  [OK] {self.name}: 批判性评审完成")
        return result
