# Code Review Agent - 设计文档

## 1. 系统概述

### 1.1 设计目标

构建一个代码审查Agent，具备：
- LLM调用能力
- Prompt设计
- 工具集成
- 上下文记忆
- 错误处理与重试

### 1.2 设计原则

1. **Agent模式优先** - 展示Agent核心设计模式，不依赖重型框架
2. **工具驱动** - 通过工具集成增强LLM能力
3. **安全第一** - 代码执行和文件读取都有安全限制
4. **可扩展** - 工具和LLM后端可轻松扩展

## 2. 架构设计

### 2.1 整体架构

```
┌──────────────────────────────────────────────┐
│                  CodeReviewAgent              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   LLM    │  │  Memory  │  │ PromptMgr│  │
│  │ Client   │  │ Manager  │  │          │  │
│  └────┬─────┘  └────┬─────┘  └──────────┘  │
│       │              │                       │
│       └──────┬───────┘                       │
│              │                                │
│  ┌───────────▼───────────┐                   │
│  │    ToolRegistry        │                   │
│  │  ┌─────────────────┐   │                   │
│  │  │  FileReader     │   │                   │
│  │  │  CodeExecutor   │   │                   │
│  │  │  ASTAnalyzer    │   │                   │
│  │  │  CodeSearch     │   │                   │
│  │  └─────────────────┘   │                   │
│  └───────────────────────┘                   │
└──────────────────────────────────────────────┘
```

### 2.2 Agent循环设计

采用ReAct（Reasoning + Acting）模式：

```
1. 接收用户输入，添加到Memory
2. 循环开始（最多max_iterations次）:
   a. 从Memory获取消息，调用LLM
   b. LLM返回响应:
      - 如果包含tool_calls → 执行工具 → 结果存入Memory → 继续循环
      - 如果无tool_calls → 返回最终响应
3. 返回响应给用户
```

### 2.3 模块职责

| 模块 | 职责 | 设计模式 |
|------|------|----------|
| CodeReviewAgent | Agent主循环，协调各组件 | Facade, Strategy |
| LLMClient | LLM API调用，重试机制 | Adapter, Retry |
| ConversationMemory | 对话历史管理 | Memento |
| PromptManager | 系统提示词和工具schema | Template |
| ToolRegistry | 工具注册和执行 | Registry, Strategy |
| 各工具类 | 具体功能实现 | Command |

## 3. 工具设计

### 3.1 工具接口

每个工具实现统一接口：

```python
def execute(self, **kwargs) -> Dict[str, Any]:
    """执行工具，返回结果字典"""
    pass
```

### 3.2 安全设计

| 工具 | 安全措施 |
|------|----------|
| FileReader | 扩展名白名单、大小限制、路径规范化 |
| CodeExecutor | 危险模块检测、危险函数检测、受限builtins |
| ASTAnalyzer | 只读分析，无安全风险 |
| CodeSearch | 结果数量限制、忽略敏感目录 |

## 4. Prompt设计

### 4.1 系统提示词

定义Agent的角色、能力、工具使用规则和输出格式。

### 4.2 工具描述

使用OpenAI function calling格式定义工具schema。

## 5. 记忆管理

### 5.1 滑动窗口策略

使用deque(maxlen=N)实现：
- 超过最大消息数时自动丢弃最旧的消息
- 保留system prompt始终在首位

### 5.2 消息格式

兼容OpenAI API格式：
- system: 系统提示
- user: 用户消息
- assistant: 助手响应（可含tool_calls）
- tool: 工具执行结果

## 6. 错误处理

### 6.1 LLM调用重试

- 指数退避重试（retry_attempts次）
- 每次重试间隔递增

### 6.2 工具执行容错

- 参数解析错误捕获
- 工具执行异常捕获，返回错误信息给LLM
- LLM可根据错误信息调整策略

## 7. 扩展性设计

### 7.1 添加新工具

1. 创建新工具类，实现execute方法
2. 在ToolRegistry._register_tools中注册
3. 在PromptManager.TOOL_SCHEMAS中添加schema

### 7.2 切换LLM后端

修改config.yaml中的llm配置即可，支持所有OpenAI兼容API。
