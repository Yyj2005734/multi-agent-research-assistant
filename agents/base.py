"""
Agent 基类

定义所有 Agent 的公共接口和行为。
每个 Agent 都有：
- name: 名称
- system_prompt: 系统提示词（定义角色）
- run(): 执行分析任务，返回结构化结果
"""

from utils.api_client import LLMClient


class BaseAgent:
    """Agent 基类，所有 Agent 继承此类"""

    # 子类必须定义的属性
    name: str = "BaseAgent"
    system_prompt: str = ""

    def __init__(self, llm_client: LLMClient):
        """
        初始化 Agent

        Args:
            llm_client: LLM API 客户端实例
        """
        self.llm = llm_client

    def run(self, user_input: str, context: str = "") -> str:
        """
        执行 Agent 任务

        Args:
            user_input: 用户的原始输入
            context: 前序 Agent 的分析结果（用于上下文传递）

        Returns:
            本 Agent 的分析结果（Markdown 格式文本）
        """
        raise NotImplementedError("子类必须实现 run() 方法")

    def _build_message(self, user_input: str, context: str = "") -> str:
        """
        构建发送给 LLM 的完整消息

        将用户输入和前序 Agent 的上下文拼接，
        确保每个 Agent 能看到前面的分析结果。

        Args:
            user_input: 原始用户输入
            context: 前序 Agent 的结果

        Returns:
            拼接后的完整消息
        """
        if context:
            return (
                f"【原始输入】\n{user_input}\n\n"
                f"【前序 Agent 的分析结果】\n{context}"
            )
        return user_input

    def __repr__(self):
        return f"<{self.name}>"
