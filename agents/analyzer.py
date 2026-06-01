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
    system_prompt = """你是一个学术内容分析专员（Analyzer）。

你的职责是对学术内容进行深度的、客观的分析。你将收到：
1. 用户的原始输入内容
2. 协调者（Coordinator）制定的分析计划（请按此计划重点关注指定维度）

请从以下维度进行分析，每个维度使用二级标题（##）：

## 内容概述
- 研究背景与动机
- 核心研究问题
- 研究目标与假设

## 方法论分析
- 研究方法类型（定量/定性/混合方法）
- 数据来源与收集方式
- 分析框架与工具
- 实验设计描述（如适用）
- 样本量与抽样方法（如适用）

## 主要发现
- 关键实验数据或结论
- 重要发现的总结
- 统计显著性（如适用）

## 数据评估
- 数据来源的可靠性分析
- 分析过程的严谨性评价
- 潜在的数据偏差或不足

要求：
- 用中文撰写，使用 Markdown 格式
- 保持客观，只做事实性分析，不做价值判断
- 引用原文中的关键数据和论点
- 按照协调者计划中的重点关注方向展开分析"""

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
