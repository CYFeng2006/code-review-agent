"""
Prompt设计 - 管理系统提示词和Prompt模板
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class PromptManager:
    """Prompt管理器 - 管理系统提示词和各类Prompt模板"""

    # 系统提示词 - 定义Agent的角色和行为
    SYSTEM_PROMPT = """你是一个专业的代码审查Agent（Code Review Agent）。
你的职责是分析代码质量、发现潜在Bug、给出改进建议。

## 你的能力
1. **代码审查**: 分析代码结构、风格、安全性、可维护性
2. **Bug发现**: 识别空指针、类型错误、边界条件、资源泄漏等常见Bug
3. **改进建议**: 给出具体的重构和优化建议
4. **代码解释**: 解释代码逻辑和执行流程

## 工具使用规则
- 使用 `read_file` 读取代码文件内容
- 使用 `execute_code` 执行代码片段验证逻辑
- 使用 `analyze_ast` 分析Python代码的AST结构
- 使用 `search_code` 在目录中搜索代码

## 输出格式
请使用Markdown格式输出审查结果，包括：
- 概述（总体评价）
- 发现的问题（按严重程度排列）
- 改进建议（具体可操作的建议）
- 代码示例（展示改进后的代码）

## 行为准则
- 先使用工具读取代码，再进行分析
- 给出具体、可操作的改进建议
- 指出问题时附带代码行号
- 保持客观专业的态度
"""

    # 工具描述（OpenAI function calling格式）
    TOOL_SCHEMAS: List[Dict] = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "读取指定路径的代码文件内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要读取的文件路径"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_code",
                "description": "执行Python代码片段并返回输出结果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的Python代码"
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_ast",
                "description": "分析Python代码的AST（抽象语法树）结构",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要分析的Python代码"
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_code",
                "description": "在指定目录中搜索代码文件和内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "搜索的目录路径"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "搜索关键词或正则表达式"
                        }
                    },
                    "required": ["directory", "pattern"]
                }
            }
        }
    ]

    @classmethod
    def get_system_prompt(cls) -> str:
        """获取系统提示词"""
        return cls.SYSTEM_PROMPT

    @classmethod
    def get_tool_schemas(cls) -> List[Dict]:
        """获取工具描述（OpenAI格式）"""
        return cls.TOOL_SCHEMAS

    @classmethod
    def get_welcome_message(cls) -> str:
        """获取欢迎消息"""
        return (
            "# Code Review Agent 已启动\n\n"
            "我是一个专业的代码审查助手，可以帮你：\n"
            "- **审查代码质量** - 分析代码结构、风格、安全性\n"
            "- **发现潜在Bug** - 空指针、类型错误、边界条件等\n"
            "- **给出改进建议** - 具体的重构和优化方案\n"
            "- **解释代码逻辑** - 理解代码执行流程\n\n"
            "你可以：\n"
            "1. 让我审查某个文件：`审查 examples/example1.py`\n"
            "2. 直接粘贴代码让我分析\n"
            "3. 让我搜索项目中的代码：`搜索 /path/to/project 中的函数定义`\n"
            "4. 输入 `help` 查看帮助\n"
            "5. 输入 `clear` 清空对话历史\n"
            "6. 输入 `exit` 退出\n"
        )

    @classmethod
    def format_review_request(cls, file_path: str) -> str:
        """格式化审查请求"""
        return f"请审查文件 `{file_path}` 的代码质量，分析潜在Bug并给出改进建议。"
