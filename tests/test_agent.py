"""
Code Review Agent - 单元测试
测试Agent核心功能、工具和记忆管理
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core import CodeReviewAgent
from agent.llm import LLMClient, LLMResponse
from agent.memory import ConversationMemory, Message
from agent.prompts import PromptManager
from agent.tools import ToolRegistry
from agent.tools.file_reader import FileReaderTool
from agent.tools.code_executor import CodeExecutorTool
from agent.tools.ast_analyzer import ASTAnalyzerTool
from agent.tools.code_search import CodeSearchTool


class TestConversationMemory:
    """测试对话记忆管理"""

    def test_init(self):
        """测试初始化"""
        memory = ConversationMemory(max_messages=10)
        assert memory.message_count == 0

    def test_init_with_system_prompt(self):
        """测试带系统提示词初始化"""
        memory = ConversationMemory(
            max_messages=10,
            system_prompt="You are a helpful assistant."
        )
        assert memory.message_count == 1
        messages = memory.get_messages()
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant."

    def test_add_messages(self):
        """测试添加消息"""
        memory = ConversationMemory(max_messages=10, system_prompt="system")
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi there")

        assert memory.message_count == 3  # system + user + assistant
        messages = memory.get_messages()
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Hi there"

    def test_max_messages_limit(self):
        """测试最大消息限制"""
        memory = ConversationMemory(max_messages=3)
        for i in range(5):
            memory.add_user_message(f"Message {i}")

        assert memory.message_count == 3  # 只保留最后3条

    def test_clear(self):
        """测试清空记忆"""
        memory = ConversationMemory(
            max_messages=10,
            system_prompt="system"
        )
        memory.add_user_message("Hello")
        memory.clear()

        assert memory.message_count == 1  # 保留system
        messages = memory.get_messages()
        assert messages[0]["role"] == "system"

    def test_context(self):
        """测试上下文存储"""
        memory = ConversationMemory(max_messages=10)
        memory.set_context("key", "value")
        assert memory.get_context("key") == "value"
        assert memory.get_context("nonexistent", "default") == "default"

    def test_get_summary(self):
        """测试摘要"""
        memory = ConversationMemory(max_messages=10, system_prompt="system")
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi")
        summary = memory.get_summary()
        assert "1条用户消息" in summary
        assert "1条助手消息" in summary


class TestLLMClient:
    """测试LLM客户端"""

    def test_init_without_api_key(self):
        """测试无API Key初始化"""
        client = LLMClient({"api_key": ""})
        assert not client.is_available

    def test_mock_response(self):
        """测试模拟响应"""
        client = LLMClient({"api_key": ""})
        messages = [{"role": "user", "content": "请审查代码"}]
        response = client.chat(messages)

        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert "代码审查报告" in response.content

    def test_mock_response_bug(self):
        """测试Bug分析模拟响应"""
        client = LLMClient({"api_key": ""})
        messages = [{"role": "user", "content": "检查bug"}]
        response = client.chat(messages)

        assert "Bug分析报告" in response.content


class TestPromptManager:
    """测试Prompt管理器"""

    def test_get_system_prompt(self):
        """测试获取系统提示词"""
        prompt = PromptManager.get_system_prompt()
        assert len(prompt) > 0
        assert "代码审查Agent" in prompt

    def test_get_tool_schemas(self):
        """测试获取工具描述"""
        schemas = PromptManager.get_tool_schemas()
        assert len(schemas) == 4

        names = [s["function"]["name"] for s in schemas]
        assert "read_file" in names
        assert "execute_code" in names
        assert "analyze_ast" in names
        assert "search_code" in names

    def test_get_welcome_message(self):
        """测试欢迎消息"""
        msg = PromptManager.get_welcome_message()
        assert "Code Review Agent" in msg
        assert "exit" in msg


class TestFileReaderTool:
    """测试文件读取工具"""

    def test_read_existing_file(self, tmpdir):
        """测试读取存在的文件"""
        # 创建临时文件
        test_file = tmpdir.join("test.py")
        test_file.write("print('Hello')\n")

        tool = FileReaderTool({"enabled": True})
        result = tool.execute(file_path=str(test_file))

        assert "error" not in result
        assert result["content"] == "print('Hello')\n"
        assert result["line_count"] == 2  # print + empty line
        assert result["language"] == "python"

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        tool = FileReaderTool({"enabled": True})
        result = tool.execute(file_path="/nonexistent/file.py")

        assert "error" in result
        assert "不存在" in result["error"]

    def test_unsupported_extension(self, tmpdir):
        """测试不支持的文件类型"""
        test_file = tmpdir.join("test.exe")
        test_file.write("binary data")

        tool = FileReaderTool({"enabled": True})
        result = tool.execute(file_path=str(test_file))

        assert "error" in result
        assert "不支持" in result["error"]

    def test_numbered_content(self, tmpdir):
        """测试带行号的内容"""
        test_file = tmpdir.join("test.py")
        test_file.write("line1\nline2\n")

        tool = FileReaderTool({"enabled": True})
        result = tool.execute(file_path=str(test_file))

        assert "numbered_content" in result
        assert "1" in result["numbered_content"]
        assert "line1" in result["numbered_content"]


class TestCodeExecutorTool:
    """测试代码执行工具"""

    def test_simple_execution(self):
        """测试简单代码执行"""
        tool = CodeExecutorTool({"enabled": True, "timeout": 5})
        result = tool.execute(code="print('Hello, World!')")

        assert result["success"] is True
        assert "Hello, World!" in result["stdout"]

    def test_math_execution(self):
        """测试数学计算"""
        tool = CodeExecutorTool({"enabled": True, "timeout": 5})
        code = "x = 10\ny = 20\nprint(x + y)"
        result = tool.execute(code=code)

        assert result["success"] is True
        assert "30" in result["stdout"]

    def test_syntax_error(self):
        """测试语法错误"""
        tool = CodeExecutorTool({"enabled": True, "timeout": 5})
        result = tool.execute(code="print('hello")

        assert result["success"] is False
        assert "语法错误" in result["error"]

    def test_security_check_import(self):
        """测试安全检查 - 禁止的模块"""
        tool = CodeExecutorTool({"enabled": True, "timeout": 5})
        result = tool.execute(code="import os\nos.system('ls')")

        assert "error" in result
        assert "安全检查" in result["error"]

    def test_security_check_eval(self):
        """测试安全检查 - eval"""
        tool = CodeExecutorTool({"enabled": True, "timeout": 5})
        result = tool.execute(code="eval('1+1')")

        assert "error" in result
        assert "安全检查" in result["error"]

    def test_runtime_error(self):
        """测试运行时错误"""
        tool = CodeExecutorTool({"enabled": True, "timeout": 5})
        result = tool.execute(code="1/0")

        assert result["success"] is False
        assert "ZeroDivisionError" in result["error"]


class TestASTAnalyzerTool:
    """测试AST分析工具"""

    def test_simple_analysis(self):
        """测试简单代码分析"""
        code = """
def hello():
    print("Hello")

class Foo:
    pass
"""
        tool = ASTAnalyzerTool({"enabled": True})
        result = tool.execute(code=code)

        assert result["success"] is True
        assert result["summary"]["functions"] == 1
        assert result["summary"]["classes"] == 1

    def test_function_extraction(self):
        """测试函数提取"""
        code = """
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b
"""
        tool = ASTAnalyzerTool({"enabled": True})
        result = tool.execute(code=code)

        assert result["success"] is True
        assert len(result["functions"]) == 1
        assert result["functions"][0]["name"] == "add"
        assert result["functions"][0]["has_docstring"] is True

    def test_missing_docstring_detection(self):
        """测试文档字符串缺失检测"""
        code = "def foo():\n    pass\n"
        tool = ASTAnalyzerTool({"enabled": True})
        result = tool.execute(code=code)

        issues = result["issues"]
        assert any(i["type"] == "missing_docstring" for i in issues)

    def test_syntax_error(self):
        """测试语法错误"""
        tool = ASTAnalyzerTool({"enabled": True})
        result = tool.execute(code="def (")

        assert "error" in result
        assert "语法错误" in result["error"]


class TestCodeSearchTool:
    """测试代码搜索工具"""

    def test_search_in_directory(self, tmpdir):
        """测试在目录中搜索"""
        # 创建测试文件
        tmpdir.join("a.py").write("def hello():\n    pass\n")
        tmpdir.join("b.py").write("def world():\n    pass\n")

        tool = CodeSearchTool({"enabled": True, "max_results": 10})
        result = tool.execute(directory=str(tmpdir), pattern="def")

        assert result["success"] is True
        assert result["total_matches"] == 2

    def test_nonexistent_directory(self):
        """测试不存在的目录"""
        tool = CodeSearchTool({"enabled": True})
        result = tool.execute(directory="/nonexistent", pattern="test")

        assert "error" in result

    def test_max_results(self, tmpdir):
        """测试最大结果限制"""
        # 创建多个文件
        for i in range(5):
            tmpdir.join(f"file_{i}.py").write(f"def func_{i}():\n    pass\n")

        tool = CodeSearchTool({"enabled": True, "max_results": 3})
        result = tool.execute(directory=str(tmpdir), pattern="def")

        assert result["total_matches"] == 3
        assert result["truncated"] is True


class TestToolRegistry:
    """测试工具注册器"""

    def test_init(self):
        """测试初始化"""
        registry = ToolRegistry({
            "file_reader": {"enabled": True},
            "code_executor": {"enabled": True},
            "ast_analyzer": {"enabled": True},
            "code_search": {"enabled": True},
        })

        assert len(registry.list_tools()) == 4
        assert registry.has_enabled_tools is True

    def test_disabled_tool(self):
        """测试禁用工具"""
        registry = ToolRegistry({
            "file_reader": {"enabled": False},
            "code_executor": {"enabled": True},
            "ast_analyzer": {"enabled": True},
            "code_search": {"enabled": True},
        })

        tools = registry.list_tools()
        assert "read_file" not in tools
        assert "execute_code" in tools

    def test_execute_nonexistent_tool(self):
        """测试执行不存在的工具"""
        registry = ToolRegistry({
            "file_reader": {"enabled": True},
            "code_executor": {"enabled": True},
            "ast_analyzer": {"enabled": True},
            "code_search": {"enabled": True},
        })

        result = registry.execute("nonexistent_tool")
        assert "error" in result


class TestCodeReviewAgent:
    """测试Agent核心"""

    def test_init(self):
        """测试Agent初始化"""
        config = {
            "llm": {"api_key": ""},
            "agent": {
                "max_iterations": 5,
                "max_memory_messages": 10,
                "retry_attempts": 2,
                "retry_delay": 0.1,
            },
            "tools": {
                "file_reader": {"enabled": True},
                "code_executor": {"enabled": True},
                "ast_analyzer": {"enabled": True},
                "code_search": {"enabled": True},
            }
        }
        agent = CodeReviewAgent(config)

        assert agent.max_iterations == 5
        assert not agent.is_llm_available  # 模拟模式

    def test_run_mock_mode(self):
        """测试模拟模式运行"""
        config = {
            "llm": {"api_key": ""},
            "agent": {
                "max_iterations": 3,
                "max_memory_messages": 10,
                "retry_attempts": 1,
                "retry_delay": 0.1,
            },
            "tools": {
                "file_reader": {"enabled": True},
                "code_executor": {"enabled": True},
                "ast_analyzer": {"enabled": True},
                "code_search": {"enabled": True},
            }
        }
        agent = CodeReviewAgent(config)
        response = agent.run("请审查代码")

        assert len(response) > 0
        assert "代码审查报告" in response

    def test_reset(self):
        """测试重置"""
        config = {
            "llm": {"api_key": ""},
            "agent": {
                "max_iterations": 3,
                "max_memory_messages": 10,
                "retry_attempts": 1,
                "retry_delay": 0.1,
            },
            "tools": {
                "file_reader": {"enabled": True},
                "code_executor": {"enabled": True},
                "ast_analyzer": {"enabled": True},
                "code_search": {"enabled": True},
            }
        }
        agent = CodeReviewAgent(config)
        agent.run("Hello")
        assert agent.memory.message_count > 1

        agent.reset()
        assert agent.memory.message_count == 1  # 只有system prompt

    def test_get_stats(self):
        """测试统计信息"""
        config = {
            "llm": {"api_key": ""},
            "agent": {
                "max_iterations": 3,
                "max_memory_messages": 10,
                "retry_attempts": 1,
                "retry_delay": 0.1,
            },
            "tools": {
                "file_reader": {"enabled": True},
                "code_executor": {"enabled": True},
                "ast_analyzer": {"enabled": True},
                "code_search": {"enabled": True},
            }
        }
        agent = CodeReviewAgent(config)
        agent.run("Test query")

        stats = agent.get_stats()
        assert stats["total_queries"] == 1
        assert stats["total_llm_calls"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
