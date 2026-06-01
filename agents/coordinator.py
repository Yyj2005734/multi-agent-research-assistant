"""
协调者 Agent（Coordinator）

职责：
1. 分析用户的自然语言需求，判断输入类型（论文/综述主题/研究问题）
2. 将复杂任务拆解为子任务，为每个 Agent 分配具体工作重点
3. 制定分析计划，指导后续 Agent 的工作方向

注意：Coordinator 不做内容分析，只做任务规划。
"""

from .base import BaseAgent


class Coordinator(BaseAgent):
    """协调者：分析需求、拆解任务、制定计划"""

    name = "Coordinator"
    system_prompt = """你是一个学术研究协调者（Coordinator）。

你的职责是分析用户的输入，制定分析计划。你不需要做内容分析，那是其他 Agent 的工作。

请完成以下任务：
1. 判断输入内容的类型（论文全文/摘要/研究主题/研究问题）
2. 识别核心研究领域和关键概念
3. 为后续的 Analyzer（分析专员）和 Reviewer（评审专员）分别制定具体的分析重点

输出格式（严格使用此 Markdown 结构）：

## 输入分析
- **类型**：（论文全文 / 论文摘要 / 研究主题 / 研究问题）
- **领域**：（所属学科领域）
- **关键词**：（3-5 个核心关键词）

## 分析计划

### 分析专员（Analyzer）重点任务
（具体说明 Analyzer 应该重点关注的内容维度，比如：
- 重点分析 XXX 方法的原理和流程
- 关注数据集的规模和来源
- 分析实验设计的合理性）

### 评审专员（Reviewer）重点任务
（具体说明 Reviewer 应该重点关注的评审维度，比如：
- 重点评估 XXX 方法与现有方法的对比优势
- 关注研究的可复现性
- 分析结论的泛化能力）

请用中文回复。"""

    def run(self, user_input: str, context: str = "") -> str:
        """
        协调者分析用户需求，制定分析计划

        Args:
            user_input: 用户的自然语言输入
            context: 此 Agent 不需要前序上下文

        Returns:
            分析计划（Markdown 格式）
        """
        print(f"  [*] {self.name}: 正在分析任务并制定计划...")
        message = self._build_message(user_input, context)
        result = self.llm.chat(self.system_prompt, message)
        print(f"  [OK] {self.name}: 分析计划制定完成")
        return result
