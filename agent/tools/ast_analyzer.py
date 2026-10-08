"""
AST分析工具 - 分析Python代码的抽象语法树结构
"""

import ast
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ASTAnalyzerTool:
    """AST分析工具 - 解析Python代码的AST，提供结构化分析"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AST分析工具

        Args:
            config: 配置字典
        """
        self.max_depth = config.get("max_depth", 10)
        logger.debug("AST分析工具已初始化")

    def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        分析Python代码的AST结构

        Args:
            code: Python代码字符串

        Returns:
            包含AST分析结果的字典
        """
        logger.info(f"分析AST（{len(code)}字符）")

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "error": f"语法错误: {e}",
                "line": e.lineno,
                "column": e.offset,
                "details": str(e.args),
            }

        # 分析结果
        result = {
            "success": True,
            "summary": self._generate_summary(tree),
            "functions": self._extract_functions(tree),
            "classes": self._extract_classes(tree),
            "imports": self._extract_imports(tree),
            "complexity": self._analyze_complexity(tree),
            "issues": self._detect_issues(tree, code),
        }

        return result

    def _generate_summary(self, tree: ast.Module) -> Dict[str, int]:
        """生成AST摘要统计"""
        summary = {
            "total_nodes": sum(1 for _ in ast.walk(tree)),
            "functions": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))),
            "classes": sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)),
            "imports": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))),
            "assignments": sum(1 for n in ast.walk(tree) if isinstance(n, ast.Assign)),
            "loops": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))),
            "conditionals": sum(1 for n in ast.walk(tree) if isinstance(n, ast.If)),
            "try_blocks": sum(1 for n in ast.walk(tree) if isinstance(n, ast.Try)),
        }
        return summary

    def _extract_functions(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """提取所有函数定义信息"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 获取参数
                args = []
                for arg in node.args.args:
                    args.append({
                        "name": arg.arg,
                        "annotation": self._get_annotation(arg.annotation),
                    })

                # 获取返回类型
                returns = self._get_annotation(node.returns)

                # 检查是否有文档字符串
                has_docstring = self._check_docstring(node) if node.body else False

                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "args": args,
                    "returns": returns,
                    "has_docstring": has_docstring,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": [self._get_decorator(d) for d in node.decorator_list],
                })
        return functions

    def _extract_classes(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """提取所有类定义信息"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 获取基类
                bases = []
                for base in node.bases:
                    bases.append(self._get_name_from_node(base))

                # 统计方法和属性
                methods = []
                attributes = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append(target.id)

                has_docstring = self._check_docstring(node) if node.body else False

                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "bases": bases,
                    "methods": methods,
                    "attributes": attributes,
                    "has_docstring": has_docstring,
                    "decorators": [self._get_decorator(d) for d in node.decorator_list],
                })
        return classes

    def _extract_imports(self, tree: ast.Module) -> List[Dict[str, str]]:
        """提取所有导入信息"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                    })
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append({
                        "type": "from",
                        "module": node.module or "",
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                    })
        return imports

    def _analyze_complexity(self, tree: ast.Module) -> Dict[str, Any]:
        """分析代码复杂度"""
        complexity = {
            "max_nesting_depth": 0,
            "total_branches": 0,
            "total_loops": 0,
            "total_statements": 0,
        }

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth = self._get_nesting_depth(node)
                complexity["max_nesting_depth"] = max(
                    complexity["max_nesting_depth"], depth
                )

            if isinstance(node, (ast.If, ast.IfExp)):
                complexity["total_branches"] += 1

            if isinstance(node, (ast.For, ast.While)):
                complexity["total_loops"] += 1

            if isinstance(node, ast.stmt):
                complexity["total_statements"] += 1

        # 计算简单复杂度评分
        score = (
            complexity["max_nesting_depth"] * 2 +
            complexity["total_branches"] +
            complexity["total_loops"] * 2
        )
        complexity["score"] = score
        complexity["level"] = (
            "低" if score < 10 else
            "中" if score < 20 else
            "高"
        )

        return complexity

    def _detect_issues(self, tree: ast.Module, code: str) -> List[Dict[str, str]]:
        """检测潜在问题"""
        issues = []

        # 检查：函数缺少文档字符串
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_docstring = self._check_docstring(node) if node.body else False
                if not has_docstring:
                    issues.append({
                        "type": "missing_docstring",
                        "severity": "warning",
                        "message": f"函数 '{node.name}' (行{node.lineno}) 缺少文档字符串",
                    })

            # 检查：过长的函数
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", node.lineno)
                func_length = end_line - node.lineno + 1
                if func_length > 50:
                    issues.append({
                        "type": "long_function",
                        "severity": "warning",
                        "message": f"函数 '{node.name}' 长达{func_length}行，建议拆分",
                    })

            # 检查：过多的参数
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_count = len(node.args.args)
                if arg_count > 5:
                    issues.append({
                        "type": "too_many_args",
                        "severity": "info",
                        "message": f"函数 '{node.name}' 有{arg_count}个参数，考虑使用参数对象",
                    })

            # 检查：bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "type": "bare_except",
                        "severity": "warning",
                        "message": f"行{node.lineno}: 使用了bare except，建议捕获具体异常",
                    })

        # 检查：全局变量
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                issues.append({
                    "type": "global_statement",
                    "severity": "info",
                    "message": f"行{node.lineno}: 使用了global语句",
                })

        return issues

    def _check_docstring(self, node: ast.AST) -> bool:
        """检查节点是否包含文档字符串"""
        if not hasattr(node, "body") or not node.body:
            return False
        first_stmt = node.body[0]
        if not isinstance(first_stmt, ast.Expr):
            return False
        value = first_stmt.value
        # Python 3.8+: ast.Constant with str value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return True
        # Python 3.7: ast.Str (removed in Python 3.12)
        StrType = getattr(ast, "Str", None)
        if StrType is not None and isinstance(value, StrType):
            return True
        return False

    def _get_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """递归获取嵌套深度"""
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._get_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._get_nesting_depth(child, depth)
                max_depth = max(max_depth, child_depth)
        return max_depth

    def _get_annotation(self, node: Any) -> str:
        """获取类型注解字符串"""
        if node is None:
            return None
        return self._get_name_from_node(node)

    def _get_name_from_node(self, node: Any) -> str:
        """从AST节点获取名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name_from_node(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name_from_node(node.value)}[{self._get_name_from_node(node.slice)}]"
        else:
            return ast.dump(node)

    def _get_decorator(self, node: Any) -> str:
        """获取装饰器名称"""
        return self._get_name_from_node(node)
