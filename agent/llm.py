"""
LLM调用层 - 封装OpenAI兼容API的调用逻辑
支持OpenAI / 通义千问 / Claude等兼容接口
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    tool_calls: List[Dict[str, Any]]
    usage: Dict[str, int]
    raw: Any = None

    @property
    def has_tool_calls(self) -> bool:
        """是否包含工具调用"""
        return len(self.tool_calls) > 0


class LLMClient:
    """LLM客户端 - 封装LLM API调用"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM客户端

        Args:
            config: LLM配置字典，包含：
                - api_key: API密钥
                - base_url: API基础URL
                - model: 模型名称
                - temperature: 温度参数
                - max_tokens: 最大token数
        """
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 2000)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 1.0)

        self._client = None
        if OpenAI and self.api_key:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"LLM客户端已初始化，模型: {self.model}")
        else:
            logger.warning("LLM客户端未正确初始化（缺少api_key或openai库）")

    @property
    def is_available(self) -> bool:
        """LLM客户端是否可用"""
        return self._client is not None

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        调用LLM进行对话

        Args:
            messages: 消息列表
            tools: 可用工具列表（OpenAI function calling格式）
            temperature: 覆盖默认温度
            max_tokens: 覆盖默认最大token数

        Returns:
            LLMResponse对象

        Raises:
            RuntimeError: 当LLM不可用或调用失败时
        """
        if not self.is_available:
            # 模拟模式 - 当没有API Key时返回模拟响应
            logger.info("LLM不可用，使用模拟模式")
            return self._mock_response(messages, tools)

        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature or self.temperature,
                    "max_tokens": max_tokens or self.max_tokens,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = self._client.chat.completions.create(**kwargs)

                # 解析响应
                message = response.choices[0].message
                tool_calls = []

                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tc in message.tool_calls:
                        tool_calls.append({
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        })

                usage = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }

                return LLMResponse(
                    content=message.content or "",
                    tool_calls=tool_calls,
                    usage=usage,
                    raw=response,
                )

            except Exception as e:
                last_error = e
                logger.warning(f"LLM调用失败（第{attempt + 1}次）: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        raise RuntimeError(
            f"LLM调用失败，重试{self.retry_attempts}次后仍错误: {last_error}"
        )

    def _mock_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]]
    ) -> LLMResponse:
        """
        模拟LLM响应（当没有API Key时使用）

        这是一个简化的模拟，用于演示和测试
        """
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg["content"]
                break

        # 简单的关键词匹配模拟
        if "review" in last_user_msg.lower() or "审查" in last_user_msg:
            content = (
                "## 代码审查报告\n\n"
                "### 概述\n代码结构整体合理，以下是审查结果：\n\n"
                "### 发现的问题\n"
                "1. **潜在Bug**: 变量可能未初始化就使用\n"
                "2. **代码风格**: 建议添加更多注释和类型标注\n"
                "3. **安全性**: 用户输入未做充分校验\n\n"
                "### 改进建议\n"
                "- 添加输入参数验证\n"
                "- 使用类型注解提高可读性\n"
                "- 考虑添加单元测试覆盖关键逻辑\n"
            )
        elif "bug" in last_user_msg.lower() or "问题" in last_user_msg:
            content = (
                "## Bug分析报告\n\n"
                "### 发现的潜在Bug\n"
                "1. **空指针风险**: 函数返回值可能为None，调用前未检查\n"
                "2. **类型错误**: 字符串与数字可能发生隐式转换\n"
                "3. **边界条件**: 循环边界可能差一（off-by-one）\n"
            )
        else:
            content = (
                "## 代码分析结果\n\n"
                "代码已接收分析。建议提供具体代码文件以获得更详细的审查报告。\n"
                "可以使用 `read_file` 工具读取代码文件，"
                "或直接粘贴代码进行分析。\n"
            )

        return LLMResponse(
            content=content,
            tool_calls=[],
            usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            raw=None,
        )
