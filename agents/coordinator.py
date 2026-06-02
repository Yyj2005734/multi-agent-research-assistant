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
    system_prompt = """你是学术研究协调者（Coordinator）。分析用户输入，制定分析计划。

任务：
1. 判断输入类型（论文全文/摘要/研究主题/研究问题）
2. 识别核心领域和关键词
3. 为 Analyzer 和 Reviewer 分别制定分析重点

输出格式：

## 输入分析
- **类型**：...
- **领域**：...
- **关键词**：3-5个

## 分析计划
### Analyzer 重点
（重点关注的内容维度，2-3条）
### Reviewer 重点
（重点关注的评审维度，2-3条）

用中文回复，简洁精炼。"""

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
