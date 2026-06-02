"""
分析 Agent（Analyzer）

职责：
1. 深度分析学术文本的核心内容
2. 提取摘要、解析方法论、梳理核心结论
3. 评估数据来源和分析过程的可靠性

注意：Analyzer 专注于事实和方法的客观分析，不做价值判断。
"""

from .base import BaseAgent


class Analyzer(BaseAgent):
    """分析专员：深度内容分析和方法论解析"""

    name = "Analyzer"
    system_prompt = """你是学术内容分析专员（Analyzer）。对学术内容做深度客观分析。

维度（每项用 ## 标题）：
## 内容概述：背景、核心问题、目标
## 方法论分析：方法类型、数据来源、实验设计、样本量
## 主要发现：关键数据、重要结论、统计显著性
## 数据评估：数据可靠性、分析严谨性、潜在偏差

要求：用中文，Markdown格式，客观分析不做价值判断，引用原文关键数据，按协调者计划的重点方向展开。"""

    def run(self, user_input: str, context: str = "") -> str:
        """
        分析专员执行深度内容分析

        Args:
            user_input: 用户原始输入
            context: Coordinator 的分析计划

        Returns:
            结构化的内容分析报告
        """
        print(f"  [*] {self.name}: 正在进行深度内容分析...")
        message = self._build_message(user_input, context)
        result = self.llm.chat(self.system_prompt, message)
        print(f"  [OK] {self.name}: 内容分析完成")
        return result
