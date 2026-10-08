"""
Agent核心模块 - 实现Agent循环（输入→推理→工具调用→输出）
"""

import json
import time
import logging
from typing import Dict, Any
from .llm import LLMClient, LLMResponse
from .memory import ConversationMemory
from .prompts import PromptManager
from .tools import ToolRegistry

logger = logging.getLogger(__name__)


class CodeReviewAgent:
    """代码审查Agent - 核心Agent类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Agent

        Args:
            config: 配置字典，包含llm、agent、tools配置
        """
        self.config = config

        # 初始化LLM客户端
        self.llm = LLMClient(config.get("llm", {}))

        # 初始化对话记忆
        agent_config = config.get("agent", {})
        self.memory = ConversationMemory(
            max_messages=agent_config.get("max_memory_messages", 20),
            system_prompt=PromptManager.get_system_prompt()
        )

        # 初始化工具注册器
        self.tools = ToolRegistry(config.get("tools", {}))

        # Agent参数
        self.max_iterations = agent_config.get("max_iterations", 10)
        self.retry_attempts = agent_config.get("retry_attempts", 3)
        self.retry_delay = agent_config.get("retry_delay", 1.0)

        # 统计信息
        self._stats = {
            "total_queries": 0,
            "total_tool_calls": 0,
            "total_llm_calls": 0,
            "total_errors": 0,
        }

        logger.info("Code Review Agent 已初始化")

    def run(self, user_input: str) -> str:
        """
        运行Agent主循环

        Agent循环流程：
        1. 接收用户输入
        2. LLM推理生成响应/工具调用
        3. 如果有工具调用，执行工具
        4. 将工具结果反馈给LLM
        5. 重复2-4直到LLM给出最终响应
        6. 输出结果

        Args:
            user_input: 用户输入

        Returns:
            Agent的最终响应
        """
        self._stats["total_queries"] += 1
        logger.info(f"Agent开始处理用户输入: {user_input[:100]}...")

        # 添加用户消息到记忆
        self.memory.add_user_message(user_input)

        # Agent循环
        final_response = ""
        for iteration in range(self.max_iterations):
            logger.info(f"Agent迭代 {iteration + 1}/{self.max_iterations}")

            try:
                # Step 1: LLM推理
                llm_response = self._call_llm()
                self._stats["total_llm_calls"] += 1

                # Step 2: 检查是否有工具调用
                if llm_response.has_tool_calls:
                    # 添加助手消息（包含工具调用）
                    self.memory.add_assistant_message(
                        content=llm_response.content,
                        tool_calls=llm_response.tool_calls
                    )

                    # Step 3: 执行工具调用
                    for tool_call in llm_response.tool_calls:
                        tool_result = self._execute_tool(tool_call)
                        self.memory.add_tool_message(
                            content=tool_result,
                            tool_call_id=tool_call["id"]
                        )
                        self._stats["total_tool_calls"] += 1

                    # 继续循环，让LLM处理工具结果
                    continue

                # Step 4: 没有工具调用，返回最终响应
                final_response = llm_response.content
                self.memory.add_assistant_message(content=final_response)
                break

            except Exception as e:
                self._stats["total_errors"] += 1
                logger.error(f"Agent迭代 {iteration + 1} 出错: {e}", exc_info=True)

                if iteration < self.max_iterations - 1:
                    logger.info(f"等待 {self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    final_response = (
                        f"## 错误\n\n"
                        f"Agent处理过程中发生错误：\n"
                        f"```\n{str(e)}\n```\n\n"
                        f"请检查配置或重试。"
                    )
                    break

        else:
            final_response = (
                f"## 超时\n\n"
                f"Agent已达到最大迭代次数（{self.max_iterations}），"
                f"请简化请求或增加配置中的max_iterations。"
            )
            logger.warning(f"Agent达到最大迭代次数: {self.max_iterations}")

        logger.info("Agent完成处理")
        return final_response

    def _call_llm(self) -> LLMResponse:
        """调用LLM进行推理"""
        messages = self.memory.get_messages()
        tools = PromptManager.get_tool_schemas()

        response = self.llm.chat(
            messages=messages,
            tools=tools if self.tools.has_enabled_tools else None
        )

        logger.debug(
            f"LLM响应: content="
            f"{response.content[:50] if response.content else 'None'}..., "
            f"tool_calls={len(response.tool_calls)}"
        )

        return response

    def _execute_tool(self, tool_call: Dict[str, Any]) -> str:
        """
        执行工具调用

        Args:
            tool_call: 工具调用信息，包含name和arguments

        Returns:
            工具执行结果（字符串）
        """
        tool_name = tool_call["name"]
        arguments = tool_call.get("arguments", "{}")

        # 解析参数
        try:
            if isinstance(arguments, str):
                args = json.loads(arguments)
            else:
                args = arguments
        except json.JSONDecodeError as e:
            error_msg = f"参数解析失败: {e}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        logger.info(f"执行工具: {tool_name}, 参数: {args}")

        # 执行工具
        result = self.tools.execute(tool_name, **args)

        # 序列化结果
        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)

    def reset(self) -> None:
        """重置Agent（清空对话记忆）"""
        self.memory.clear()
        logger.info("Agent已重置")

    def get_stats(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        stats = self._stats.copy()
        stats["memory_info"] = self.memory.get_summary()
        return stats

    @property
    def is_llm_available(self) -> bool:
        """LLM是否可用"""
        return self.llm.is_available
