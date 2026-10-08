"""
代码搜索工具 - 在目录中搜索代码文件和内容
"""

import os
import re
import fnmatch
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CodeSearchTool:
    """代码搜索工具 - 在指定目录中搜索代码文件和内容"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化代码搜索工具

        Args:
            config: 配置字典
        """
        self.max_results = config.get("max_results", 20)
        self.code_extensions = [
            ".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h"
        ]
        self.ignore_dirs = {
            "__pycache__", ".git", "node_modules", ".venv", "venv",
            "env", ".idea", ".vscode", "dist", "build"
        }
        logger.debug(f"代码搜索工具已初始化，最大结果数: {self.max_results}")

    def execute(self, directory: str, pattern: str, **kwargs) -> Dict[str, Any]:
        """
        在目录中搜索代码

        Args:
            directory: 搜索目录路径
            pattern: 搜索关键词或正则表达式

        Returns:
            包含搜索结果的字典
        """
        logger.info(f"在 {directory} 中搜索: {pattern}")

        # 安全检查
        directory = os.path.normpath(directory)
        if not os.path.exists(directory):
            return {"error": f"目录不存在: {directory}"}
        if not os.path.isdir(directory):
            return {"error": f"路径不是目录: {directory}"}

        # 准备正则
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            # 如果不是有效正则，按普通字符串搜索
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        results: List[Dict[str, Any]] = []
        files_scanned = 0

        try:
            for root, dirs, files in os.walk(directory):
                # 过滤忽略的目录
                dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

                for filename in files:
                    # 只搜索代码文件
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in self.code_extensions:
                        continue

                    filepath = os.path.join(root, filename)
                    files_scanned += 1

                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()

                        for line_num, line in enumerate(lines, 1):
                            if regex.search(line):
                                # 获取匹配上下文
                                context_start = max(0, line_num - 2)
                                context_end = min(len(lines), line_num + 1)
                                context = "".join(
                                    f"{context_start + i + 1:4d} | {lines[context_start + i].rstrip()}"
                                    for i in range(context_end - context_start)
                                )

                                results.append({
                                    "file": filepath,
                                    "file_name": filename,
                                    "line": line_num,
                                    "match": line.rstrip(),
                                    "context": context,
                                })

                                if len(results) >= self.max_results:
                                    return {
                                        "success": True,
                                        "pattern": pattern,
                                        "files_scanned": files_scanned,
                                        "total_matches": len(results),
                                        "results": results,
                                        "truncated": True,
                                    }

                    except Exception as e:
                        logger.debug(f"跳过文件 {filepath}: {e}")
                        continue

        except Exception as e:
            return {"error": f"搜索过程中出错: {e}"}

        return {
            "success": True,
            "pattern": pattern,
            "files_scanned": files_scanned,
            "total_matches": len(results),
            "results": results,
            "truncated": False,
        }
