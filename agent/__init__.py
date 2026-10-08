"""
Code Review Agent - 代码审查智能助手
基于LLM的Agent，支持代码审查、Bug发现、改进建议
"""

from .core import CodeReviewAgent
from .llm import LLMClient
from .memory import ConversationMemory
from .prompts import PromptManager

__version__ = "1.0.0"
__author__ = "Code Review Agent Team"

__all__ = [
    "CodeReviewAgent",
    "LLMClient",
    "ConversationMemory",
    "PromptManager",
]
