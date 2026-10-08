# Code Review Agent - 代码审查智能助手

> 基于LLM的Agent，支持代码审查、Bug发现、改进建议等功能

## 功能特性

- **智能代码审查** - 分析代码质量、风格、安全性、可维护性
- **Bug自动发现** - 识别空指针、类型错误、边界条件等常见Bug
- **改进建议** - 给出具体的重构和优化建议
- **多工具协同** - 文件读取、代码执行、AST分析、代码搜索
- **上下文记忆** - 支持多轮对话，保持上下文连贯
- **错误处理** - 内置重试机制和错误恢复
- **模拟模式** - 无API Key时可用模拟模式运行

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.10+ | 支持类型注解 |
| LLM接口 | OpenAI兼容API | 支持OpenAI/通义千问/Claude等 |
| Agent框架 | 原生实现 | 展示Agent核心设计模式 |
| CLI界面 | Rich | 美观的终端UI |
| 配置 | PyYAML | YAML格式配置 |
| 测试 | pytest | 完整单元测试 |

## 项目结构

```
code-review-agent/
├── agent/                    # Agent核心模块
│   ├── __init__.py           # 包入口
│   ├── core.py               # Agent核心循环
│   ├── llm.py                # LLM调用层
│   ├── memory.py             # 上下文记忆
│   ├── prompts.py            # Prompt设计
│   └── tools/                # 工具集
│       ├── __init__.py       # 工具注册器
│       ├── file_reader.py    # 文件读取工具
│       ├── code_executor.py  # 代码执行工具
│       ├── ast_analyzer.py   # AST分析工具
│       └── code_search.py    # 代码搜索工具
├── examples/                 # 示例代码
│   ├── example_good.py       # 良好代码示例
│   └── example_bad.py        # 有问题的代码示例
├── tests/                    # 测试
│   └── test_agent.py         # 单元测试
├── config.yaml               # 配置文件
├── main.py                   # 入口文件
├── requirements.txt          # 依赖
├── README.md                 # 项目说明
├── Design.md                 # 设计文档
└── LICENSE                   # MIT协议
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`，设置你的LLM API Key：

```yaml
llm:
  api_key: "sk-your-api-key-here"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"
```

> 支持的LLM提供商：
> - OpenAI: `base_url: "https://api.openai.com/v1"`
> - 通义千问: `base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"`
> - 其他OpenAI兼容接口

> 注意：即使不配置API Key，Agent也可以在模拟模式下运行（用于演示和测试）。

### 3. 运行

#### 交互式CLI模式

```bash
python main.py
```

启动后可以输入：
- 审查某个文件：`审查 examples/example_bad.py`
- 粘贴代码直接分析
- `help` 查看帮助
- `tools` 查看可用工具
- `stats` 查看统计
- `clear` 清空对话
- `exit` 退出

#### 直接审查文件

```bash
python main.py --file examples/example_bad.py
```

## 工具说明

| 工具 | 功能 | 安全特性 |
|------|------|----------|
| `read_file` | 读取代码文件 | 扩展名白名单、大小限制 |
| `execute_code` | 执行Python代码 | 危险模块检测、安全沙箱 |
| `analyze_ast` | AST结构分析 | 复杂度计算、问题检测 |
| `search_code` | 目录代码搜索 | 正则支持、结果限制 |

## 配置说明

`config.yaml` 包含以下配置段：

### LLM配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `api_key` | "" | LLM API密钥 |
| `base_url` | OpenAI默认 | API地址 |
| `model` | gpt-4o-mini | 模型名称 |
| `temperature` | 0.3 | 温度参数 |
| `max_tokens` | 2000 | 最大token数 |

### Agent配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_iterations` | 10 | Agent最大迭代次数 |
| `max_memory_messages` | 20 | 记忆窗口大小 |
| `retry_attempts` | 3 | 重试次数 |
| `retry_delay` | 1.0 | 重试延迟(秒) |

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_agent.py::TestASTAnalyzerTool -v
```

## Agent架构

Agent采用经典的ReAct模式：

```
用户输入 → LLM推理 → 是否需要工具？
              ↓ 是
         执行工具 → 结果反馈给LLM → LLM推理
              ↓ 否
         输出最终响应
```

详见 [Design.md](Design.md)

## License

MIT License - 详见 [LICENSE](LICENSE)
