"""
综合 Agent（Synthesizer）

职责：
1. 整合所有前序 Agent 的分析结果（计划+分析+评审）
2. 构建逻辑连贯的综合报告
3. 确保报告结构规范、内容一致

注意：Synthesizer 不产生新的分析，只做整合和综合。
"""

from .base import BaseAgent


class Synthesizer(BaseAgent):
    """综合专员：整合分析结果，生成综合报告"""

    name = "Synthesizer"
    system_prompt = """你是学术综合专家（Synthesizer）。整合所有Agent的分析结果为一份综合报告。

章节（每项用 ## 标题）：
## 研究概述：背景、核心问题、目标
## 核心发现与贡献：最重要的发现和学术贡献
## 方法论评价：优势与不足的平衡评价
## 创新性分析：核心创新点、与现有研究对比
## 问题与局限：主要不足
## 综合评价：整体质量、优势、改进方向

要求：用中文，Markdown格式，提炼综合不重复原文，逻辑连贯有过渡，引用关键数据支撑评价。"""

    def run(self, user_input: str, context: str = "") -> str:
        """
        综合专员整合所有分析结果

        Args:
            user_input: 用户原始输入
            context: 所有前序 Agent 的结果汇总

        Returns:
            综合分析报告
        """
        print(f"  [*] {self.name}: 正在整合分析结果...")
        message = self._build_message(user_input, context)
        result = self.llm.chat(self.system_prompt, message)
        print(f"  [OK] {self.name}: 综合报告生成完成")
        return result
