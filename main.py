#!/usr/bin/env python3
"""
Code Review Agent - 入口文件
代码审查智能助手Agent

使用方法:
    python main.py                    # 启动交互式CLI
    python main.py --file path/to/code.py  # 审查指定文件
    python main.py --help             # 查看帮助
"""

import sys
import os
import argparse
import logging
import yaml

# 尝试导入rich用于美化输出
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.prompt import Prompt
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("提示: 安装rich库可获得更好的显示效果: pip install rich")

# 添加项目根目录到path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import CodeReviewAgent
from agent.prompts import PromptManager

# 日志配置
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent.log"),
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    # 尝试加载本地配置（优先）
    local_config = config_path.replace(".yaml", ".local.yaml")
    if os.path.exists(local_config):
        config_path = local_config

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info(f"配置已加载: {config_path}")
    else:
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        config = {
            "llm": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            "agent": {
                "max_iterations": 10,
                "max_memory_messages": 20,
                "retry_attempts": 3,
                "retry_delay": 1.0,
            },
            "tools": {
                "code_executor": {"enabled": True, "timeout": 10},
                "file_reader": {"enabled": True},
                "ast_analyzer": {"enabled": True},
                "code_search": {"enabled": True},
            }
        }
    return config


def print_output(text: str, console=None):
    """输出结果（支持rich美化）"""
    if RICH_AVAILABLE and console:
        console.print(Markdown(text))
    else:
        print(text)


def run_interactive(agent: CodeReviewAgent):
    """运行交互式CLI"""
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel(
            Markdown(PromptManager.get_welcome_message()),
            title="Code Review Agent",
            border_style="cyan"
        ))

        if not agent.is_llm_available:
            console.print("[yellow]⚠ LLM API Key未配置，使用模拟模式运行。[/yellow]")
            console.print("[dim]请在 config.yaml 中设置 api_key 以启用完整功能。[/dim]\n")
    else:
        print(PromptManager.get_welcome_message())
        if not agent.is_llm_available:
            print("\n⚠ LLM API Key未配置，使用模拟模式运行。")
            print("请在 config.yaml 中设置 api_key 以启用完整功能。\n")
        console = None

    # 交互循环
    while True:
        try:
            if RICH_AVAILABLE and console:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            else:
                user_input = input("\nYou > ").strip()

            if not user_input:
                continue

            # 特殊命令
            lower = user_input.lower()
            if lower in ("exit", "quit", "q", "退出"):
                print_output("再见！", console)
                break
            elif lower == "clear" or lower == "清空":
                agent.reset()
                print_output("对话历史已清空。", console)
                continue
            elif lower == "help" or lower == "帮助":
                print_output(PromptManager.get_welcome_message(), console)
                continue
            elif lower == "stats" or lower == "统计":
                stats = agent.get_stats()
                if RICH_AVAILABLE and console:
                    table = Table(title="Agent统计信息")
                    table.add_column("指标", style="cyan")
                    table.add_column("值", style="green")
                    for k, v in stats.items():
                        table.add_row(k, str(v))
                    console.print(table)
                else:
                    for k, v in stats.items():
                        print(f"  {k}: {v}")
                continue
            elif lower == "tools" or lower == "工具":
                tools = agent.tools.get_tool_info()
                print_output("\n".join(
                    f"- **{t['name']}**: {t['description']}" for t in tools
                ), console)
                continue

            # 运行Agent
            if RICH_AVAILABLE and console:
                console.print("[dim]Agent思考中...[/dim]")

            response = agent.run(user_input)

            if RICH_AVAILABLE and console:
                console.print(Panel(
                    Markdown(response),
                    title="[bold green]Agent[/bold green]",
                    border_style="green"
                ))
            else:
                print(f"\nAgent > {response}")

        except KeyboardInterrupt:
            print_output("\n再见！", console)
            break
        except EOFError:
            print_output("\n再见！", console)
            break
        except Exception as e:
            logger.error(f"交互错误: {e}", exc_info=True)
            print_output(f"发生错误: {e}", console)


def run_file_review(agent: CodeReviewAgent, file_path: str):
    """直接审查文件"""
    request = PromptManager.format_review_request(file_path)
    response = agent.run(request)
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel(
            Markdown(response),
            title=f"审查结果: {file_path}",
            border_style="cyan"
        ))
    else:
        print(response)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Code Review Agent - 代码审查智能助手"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "--file", "-f",
        help="直接审查指定文件"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 加载配置
    config = load_config(args.config)

    # 创建Agent
    agent = CodeReviewAgent(config)

    if args.file:
        run_file_review(agent, args.file)
    else:
        run_interactive(agent)


if __name__ == "__main__":
    main()
