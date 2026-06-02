"""
LLM API 客户端封装

统一管理 OpenAI API 的调用，支持：
- 普通调用（同步返回完整结果）
- 流式调用（逐块 yield，用于实时展示）
- 错误重试和异常处理
"""

import os
import time
from openai import OpenAI
from openai import AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()


class LLMClient:
    """LLM API 客户端，封装 OpenAI API 调用"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        max_retries: int = 2,
        timeout: int = 120,
    ):
        """
        初始化 LLM 客户端

        参数优先级：直接传入 > 环境变量 > 默认值
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_retries = max_retries
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "未配置 API Key！请通过以下方式之一配置：\n"
                "  1. 设置环境变量 OPENAI_API_KEY\n"
                "  2. 在 .env 文件中添加 OPENAI_API_KEY=sk-xxx\n"
                "  3. 初始化时传入 api_key 参数"
            )

        # 创建 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        普通调用：发送消息并返回完整响应

        Args:
            system_prompt: 系统提示词（定义 Agent 角色）
            user_message: 用户消息（要分析的内容）
            temperature: 温度参数，控制输出随机性（0-2）
            max_tokens: 最大输出 token 数

        Returns:
            完整的响应文本

        Raises:
            RuntimeError: API 调用失败且重试耗尽
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                return response.choices[0].message.content

            except AuthenticationError as e:
                # 认证错误（401）不重试，直接报错
                raise RuntimeError(f"API Key 无效或已过期，请检查配置。({e})")
            except APITimeoutError as e:
                # 超时错误
                if attempt < self.max_retries:
                    wait_time = 3
                    print(f"  [超时] 等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"API 请求超时（{self.timeout}s），请检查网络或增大超时时间。({e})")
            except APIConnectionError as e:
                # 连接错误
                if attempt < self.max_retries:
                    wait_time = 3
                    print(f"  [连接失败] 等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"无法连接到 API 服务，请检查网络和 API Base URL 配置。({e})")
            except RateLimitError as e:
                # 限流错误，等待后重试
                if attempt < self.max_retries:
                    wait_time = 5
                    print(f"  [限流] 等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"API 调用频率超限，请稍后重试。({e})")
            except Exception as e:
                err_msg = str(e)
                if "401" in err_msg or "invalid_api_key" in err_msg.lower() or "invalid key" in err_msg.lower():
                    raise RuntimeError(f"API Key 无效，请检查配置。({e})")
                if "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
                    raise RuntimeError(f"API 请求超时，请检查网络连接或 API 地址是否正确。({e})")
                if "connection" in err_msg.lower() or "connect" in err_msg.lower():
                    raise RuntimeError(f"无法连接到 API 服务 ({self.base_url})，请检查网络和 API Base URL 配置。({e})")
                if attempt < self.max_retries:
                    wait_time = 2
                    print(f"  [重试] 第 {attempt} 次失败，{wait_time}s 后重试: {e}")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"API 调用失败: {e}")

    def chat_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        流式调用：逐块 yield 响应内容

        用于 CLI 实时输出或 SSE 推送给前端

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            str: 每次产出一个文本片段（delta）

        Raises:
            RuntimeError: API 调用失败
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except Exception as e:
            raise RuntimeError(f"流式 API 调用失败: {e}")

    def test_connection(self) -> dict:
        """
        测试 API 连接是否正常

        Returns:
            dict: {"success": bool, "message": str, "model": str}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return {
                "success": True,
                "message": "连接成功",
                "model": self.model,
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "model": self.model,
            }
