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
    system_prompt = """你是一个学术综合专家（Synthesizer）。

你的职责是将多个 Agent 的分析结果整合成一份结构完整、逻辑清晰的综合报告。你将收到：
1. 用户的原始输入内容
2. 前序所有 Agent 的分析结果（协调者计划、分析专员报告、评审专员报告）

请生成一份完整的学术分析综合报告，包含以下章节（每个用一级标题 #）：

# 综合分析报告

## 研究概述
（基于协调者和分析专员的分析，给出清晰的研究全貌：
研究背景、核心问题、研究目标）

## 核心发现与贡献
（综合分析专员的方法论分析和评审专员的创新性评估，
提炼最重要的发现和学术贡献）

## 方法论评价
（结合分析专员的方法论分析和评审专员的方法论评审，
给出平衡的评价：优势 + 不足）

## 创新性分析
（基于评审专员的创新性评估，总结研究的核心创新点，
与现有研究对比分析）

## 问题与局限
（基于评审专员的局限性分析，总结主要问题和不足）

## 综合评价
（给出整体的学术评价：
- 研究的整体质量和学术价值
- 主要优势和核心贡献
- 关键不足和改进方向）

要求：
- 用中文撰写，使用 Markdown 格式
- 确保报告逻辑连贯，各章节之间有合理的过渡
- 综合多方观点，给出平衡的评价
- 不要重复前序 Agent 的完整内容，而要提炼和综合
- 引用关键数据和论点支撑你的评价"""

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
