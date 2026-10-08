"""
工具注册器 - 管理所有可用工具
"""

import logging
from typing import Dict, List, Any, Optional
from .file_reader import FileReaderTool
from .code_executor import CodeExecutorTool
from .ast_analyzer import ASTAnalyzerTool
from .code_search import CodeSearchTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册器 - 注册、管理和执行工具"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化工具注册器

        Args:
            config: 工具配置字典
        """
        self._tools: Dict[str, Any] = {}
        self._config = config

        # 注册所有工具
        self._register_tools()
        logger.info(f"工具注册器已初始化，已注册 {len(self._tools)} 个工具")

    def _register_tools(self) -> None:
        """注册所有工具"""
        # 文件读取工具
        fr_config = self._config.get("file_reader", {})
        if fr_config.get("enabled", True):
            self._tools["read_file"] = FileReaderTool(fr_config)
            logger.info("已注册工具: read_file")

        # 代码执行工具
        ce_config = self._config.get("code_executor", {})
        if ce_config.get("enabled", True):
            self._tools["execute_code"] = CodeExecutorTool(ce_config)
            logger.info("已注册工具: execute_code")

        # AST分析工具
        ast_config = self._config.get("ast_analyzer", {})
        if ast_config.get("enabled", True):
            self._tools["analyze_ast"] = ASTAnalyzerTool(ast_config)
            logger.info("已注册工具: analyze_ast")

        # 代码搜索工具
        cs_config = self._config.get("code_search", {})
        if cs_config.get("enabled", True):
            self._tools["search_code"] = CodeSearchTool(cs_config)
            logger.info("已注册工具: search_code")

    def execute(self, tool_name: str, **kwargs) -> Any:
        """
        执行指定工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果

        Raises:
            ValueError: 工具不存在时
        """
        if tool_name not in self._tools:
            error_msg = f"工具 '{tool_name}' 不存在。可用工具: {list(self._tools.keys())}"
            logger.error(error_msg)
            return {"error": error_msg}

        tool = self._tools[tool_name]
        try:
            result = tool.execute(**kwargs)
            logger.info(f"工具 {tool_name} 执行完成")
            return result
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行失败: {e}", exc_info=True)
            return {"error": f"工具执行失败: {str(e)}"}

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    @property
    def has_enabled_tools(self) -> bool:
        """是否有已启用的工具"""
        return len(self._tools) > 0

    def get_tool_info(self) -> List[Dict[str, str]]:
        """获取所有工具信息"""
        info = []
        for name, tool in self._tools.items():
            info.append({
                "name": name,
                "description": tool.__class__.__doc__ or "无描述",
            })
        return info
