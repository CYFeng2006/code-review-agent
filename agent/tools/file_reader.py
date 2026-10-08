"""
文件读取工具 - 读取代码文件内容
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FileReaderTool:
    """文件读取工具 - 读取指定路径的代码文件内容"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件读取工具

        Args:
            config: 配置字典
        """
        self.max_file_size = config.get("max_file_size", 1048576)  # 默认1MB
        self.allowed_extensions = config.get(
            "allowed_extensions",
            [".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".txt", ".md"]
        )
        logger.debug(f"文件读取工具已初始化，最大文件: {self.max_file_size}字节")

    def execute(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            包含文件内容和元信息的字典
        """
        logger.info(f"读取文件: {file_path}")

        # 安全检查：路径规范化和目录穿越防护
        file_path = os.path.normpath(file_path)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {"error": f"文件不存在: {file_path}"}

        if not os.path.isfile(file_path):
            return {"error": f"路径不是文件: {file_path}"}

        # 检查文件扩展名
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.allowed_extensions:
            return {
                "error": f"不支持的文件类型: {ext}。"
                         f"支持的类型: {', '.join(self.allowed_extensions)}"
            }

        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            return {
                "error": f"文件过大: {file_size}字节。"
                         f"最大支持: {self.max_file_size}字节"
            }

        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 添加行号
            lines = content.split("\n")
            numbered_content = "\n".join(
                f"{i + 1:4d} | {line}" for i, line in enumerate(lines)
            )

            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_size,
                "line_count": len(lines),
                "language": self._detect_language(ext),
                "content": content,
                "numbered_content": numbered_content,
            }

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, "r", encoding="gbk") as f:
                    content = f.read()
                lines = content.split("\n")
                numbered_content = "\n".join(
                    f"{i + 1:4d} | {line}" for i, line in enumerate(lines)
                )
                return {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "file_size": file_size,
                    "line_count": len(lines),
                    "language": self._detect_language(ext),
                    "content": content,
                    "numbered_content": numbered_content,
                }
            except Exception as e:
                return {"error": f"文件编码读取失败: {e}"}

        except Exception as e:
            return {"error": f"文件读取失败: {e}"}

    def _detect_language(self, ext: str) -> str:
        """根据扩展名检测语言"""
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".txt": "text",
            ".md": "markdown",
        }
        return lang_map.get(ext.lower(), "unknown")
