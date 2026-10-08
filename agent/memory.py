"""
上下文记忆管理 - 管理对话历史和上下文窗口
"""

import logging
from typing import Dict, List, Optional, Any
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """对话消息数据类"""
    role: str  # system | user | assistant | tool
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(self, max_messages: int = 20, system_prompt: Optional[str] = None):
        """
        初始化对话记忆

        Args:
            max_messages: 最大保留消息数
            system_prompt: 系统提示词
        """
        self.max_messages = max_messages
        self._messages: deque = deque(maxlen=max_messages)
        self._system_prompt = system_prompt

        if system_prompt:
            self._messages.append(Message(
                role="system",
                content=system_prompt
            ))

        # 额外的上下文存储（不参与消息窗口轮换）
        self._context: Dict[str, Any] = {}

        logger.info(f"对话记忆已初始化，最大消息数: {max_messages}")

    def add_user_message(self, content: str, **metadata) -> None:
        """添加用户消息"""
        self._messages.append(Message(
            role="user",
            content=content,
            metadata=metadata
        ))
        logger.debug(f"添加用户消息: {content[:50]}...")

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict]] = None,
        **metadata
    ) -> None:
        """添加助手消息"""
        self._messages.append(Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            metadata=metadata
        ))
        logger.debug(f"添加助手消息: {content[:50]}...")

    def add_tool_message(self, content: str, tool_call_id: str, **metadata) -> None:
        """添加工具响应消息"""
        self._messages.append(Message(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            metadata=metadata
        ))
        logger.debug(f"添加工具消息: {content[:50]}...")

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        获取当前对话消息列表（转换为OpenAI格式）

        Returns:
            OpenAI格式的消息列表
        """
        result = []
        for msg in self._messages:
            entry = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls
            result.append(entry)
        return result

    def set_context(self, key: str, value: Any) -> None:
        """设置额外上下文"""
        self._context[key] = value
        logger.debug(f"设置上下文: {key}")

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取额外上下文"""
        return self._context.get(key, default)

    def clear(self) -> None:
        """清空对话记忆（保留system prompt）"""
        self._messages.clear()
        self._context.clear()
        if self._system_prompt:
            self._messages.append(Message(
                role="system",
                content=self._system_prompt
            ))
        logger.info("对话记忆已清空")

    @property
    def message_count(self) -> int:
        """当前消息数"""
        return len(self._messages)

    def get_summary(self) -> str:
        """获取对话摘要"""
        user_msgs = sum(1 for m in self._messages if m.role == "user")
        assistant_msgs = sum(1 for m in self._messages if m.role == "assistant")
        tool_msgs = sum(1 for m in self._messages if m.role == "tool")
        return (
            f"对话历史: {user_msgs}条用户消息, "
            f"{assistant_msgs}条助手消息, {tool_msgs}条工具消息"
        )
