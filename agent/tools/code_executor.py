"""
代码执行工具 - 安全地执行Python代码片段
"""

import sys
import io
import os
import re
import traceback
import logging
from typing import Dict, Any, List
from contextlib import redirect_stdout, redirect_stderr

logger = logging.getLogger(__name__)


class CodeExecutorTool:
    """代码执行工具 - 在受限环境中执行Python代码片段"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化代码执行工具

        Args:
            config: 配置字典
        """
        self.timeout = config.get("timeout", 10)
        self.allowed_modules = set(config.get(
            "allowed_modules",
            ["math", "json", "re", "collections", "itertools", "functools"]
        ))
        # 禁止的模块和函数
        self._forbidden_modules = {
            "subprocess", "shutil", "ctypes", "multiprocessing",
            "socket", "http", "urllib", "os", "pty"
        }
        logger.debug(f"代码执行工具已初始化，超时: {self.timeout}秒")

    def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        执行Python代码片段

        Args:
            code: 要执行的Python代码

        Returns:
            包含执行结果、输出和错误的字典
        """
        logger.info(f"执行代码片段（{len(code)}字符）")

        # 安全检查
        security_check = self._security_check(code)
        if security_check:
            return {"error": f"安全检查未通过: {security_check}"}

        # 准备执行环境
        global_vars = {
            "__builtins__": self._get_safe_builtins(),
            "__name__": "__main__",
        }
        local_vars = {}

        # 捕获输出
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        start_time = __import__("time").time()

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # 使用exec执行代码
                exec(code, global_vars, local_vars)

            execution_time = __import__("time").time() - start_time

            # 获取输出
            stdout = stdout_buffer.getvalue()
            stderr = stderr_buffer.getvalue()

            result = {
                "success": True,
                "stdout": stdout if stdout else "(无输出)",
                "stderr": stderr if stderr else "",
                "execution_time": f"{execution_time:.4f}秒",
                "variables": self._extract_variables(local_vars),
            }

            return result

        except SyntaxError as e:
            execution_time = __import__("time").time() - start_time
            return {
                "success": False,
                "error": f"语法错误: {e}",
                "error_type": "SyntaxError",
                "line": e.lineno,
                "details": str(e.args),
                "execution_time": f"{execution_time:.4f}秒",
            }

        except Exception as e:
            execution_time = __import__("time").time() - start_time
            return {
                "success": False,
                "error": f"{type(e).__name__}: {e}",
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "execution_time": f"{execution_time:.4f}秒",
            }

    def _security_check(self, code: str) -> str:
        """
        安全检查 - 检测危险代码模式

        Returns:
            发现的安全问题字符串，无问题返回空字符串
        """
        # 检查禁止的模块
        for module in self._forbidden_modules:
            pattern = rf"import\s+{module}|from\s+{module}"
            if re.search(pattern, code):
                return f"禁止使用模块: {module}"

        # 检查危险函数调用
        dangerous_patterns = [
            (r"exec\s*\(", "exec()调用"),
            (r"eval\s*\(", "eval()调用"),
            (r"__import__\s*\(", "__import__()调用"),
            (r"open\s*\([^)]*['\"]w", "文件写入操作"),
            (r"open\s*\([^)]*['\"]a", "文件追加操作"),
            (r"compile\s*\(", "compile()调用"),
            (r"globals\s*\(\s*\)", "globals()调用"),
            (r"locals\s*\(\s*\)", "locals()调用"),
            (r"vars\s*\(\s*\)", "vars()调用"),
            (r"getattr\s*\([^,]*['\"]__", "getattr访问特殊属性"),
        ]

        for pattern, desc in dangerous_patterns:
            if re.search(pattern, code):
                return f"检测到危险操作: {desc}"

        return ""

    def _get_safe_builtins(self) -> Dict[str, Any]:
        """获取安全的内置函数集合"""
        safe_builtins = {}
        safe_names = [
            "print", "len", "range", "enumerate", "zip", "map", "filter",
            "sorted", "reversed", "sum", "min", "max", "abs", "round",
            "isinstance", "issubclass", "type", "str", "int", "float",
            "bool", "list", "dict", "set", "tuple", "frozenset",
            "any", "all", "repr", "format", "chr", "ord", "hex", "oct", "bin",
            "divmod", "pow", "input", "getattr",
        ]
        for name in safe_names:
            if name in __builtins__ if isinstance(__builtins__, dict) else hasattr(__builtins__, name):
                try:
                    safe_builtins[name] = __builtins__[name] if isinstance(__builtins__, dict) else getattr(__builtins__, name)
                except Exception:
                    pass
        return safe_builtins

    def _extract_variables(self, local_vars: Dict) -> Dict[str, str]:
        """提取执行后的变量（过滤特殊变量）"""
        result = {}
        for name, value in local_vars.items():
            if name.startswith("_"):
                continue
            try:
                repr_val = repr(value)
                if len(repr_val) > 200:
                    repr_val = repr_val[:200] + "..."
                result[name] = f"{type(value).__name__}: {repr_val}"
            except Exception:
                result[name] = "<无法显示>"
        return result
