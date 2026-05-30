[English](README.md) | [中文](README_CN.md)

# 📡 Radar Agent

**AI 驱动的竞争情报智能体** — 监控竞争对手、追踪趋势，从 GitHub、Hacker News、Product Hunt、RSS 订阅源等平台获取可执行的洞察。

Radar 从多个平台收集信号，使用 Claude AI 分析模式并提取洞察，然后生成结构化的情报摘要。

## 功能特性

- 🔍 **多源监控** — GitHub 仓库/组织/话题、Hacker News、Product Hunt、RSS 订阅源、网页
- 🧠 **AI 驱动分析** — Claude 过滤噪音、评估相关性、发现模式并生成可执行洞察
- 📊 **结构化摘要** — 整洁的 Markdown 和 JSON 报告，包含执行摘要、热门故事、趋势和待办事项
- 🔧 **CLI 界面** — 简单命令即可配置、运行和管理情报流水线
- 🌐 **多语言支持** — 支持中文（默认）或英文摘要
- 🛡️ **弹性设计** — 每个收集器独立运行；单个数据源的错误不会影响整个流水线

## 快速开始

### 安装

```bash
# 使用 pipx 安装（推荐）
pipx install https://github.com/Jaxz714/radar-agent/archive/main.zip

# 或使用 pip 安装
pip install https://github.com/Jaxz714/radar-agent/archive/main.zip
```

### 配置

```bash
# 初始化配置
radar init

# 设置 API 密钥（或使用 ANTHROPIC_API_KEY 环境变量）
export ANTHROPIC_API_KEY=sk-ant-...

# 添加监控目标
radar add -r anthropics/claude-code -r openai/openai-python
radar add -k "AI agent" -k "LLM" -k "Claude"
radar add -o anthropics
radar add -t ai-agent
radar add -f https://blog.anthropic.com/rss.xml
```

或直接编辑 `~/.radar/config.yaml`：

```yaml
watch:
  github_repos:
    - anthropics/claude-code
    - openai/openai-python
    - facebook/react
  github_orgs:
    - anthropics
  github_topics:
    - ai-agent
    - llm
  hackernews_keywords:
    - AI agent
    - LLM
    - Claude
  rss_feeds:
    - https://blog.anthropic.com/rss.xml
```

### 运行

```bash
# 运行完整流水线
radar run

# 仅运行特定数据源
radar run -s github -s hackernews

# 详细输出
radar run -v

# 检查配置状态
radar doctor
```

## 输出结果

摘要保存在 `~/.radar/digests/` 目录下，格式为 Markdown 和/或 JSON。

### Markdown 摘要

```markdown
# 📡 Radar 情报摘要

> **日期:** 2026-05-30 | **分析信号数:** 42

## 📋 执行摘要
今日关键动态：Anthropic 发布了 Claude 4.5，具备...

## 🔥 热门故事
### 1. 🚀 Claude 4.5 发布
**评分:** 9/10 | **类别:** 发布
新模型具备更强的推理能力...

## 📈 新兴趋势
### MCP 生态整合
**证据:** GitHub 和 HN 上出现 3 条相关信号

## ✅ 待办事项
- 🔴 [高优先级] 评估新 Claude 4.5 API 变更以进行集成
```

## 架构设计

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│  Collectors  │────▶│   Analyzer   │────▶│  Formatter  │────▶│  Output  │
│             │     │   (Claude)   │     │             │     │          │
│ • GitHub    │     │ • Filter     │     │ • Markdown  │     │ • File   │
│ • HN        │     │ • Score      │     │ • JSON      │     │ • Console│
│ • PH        │     │ • Connect    │     │             │     │          │
│ • RSS       │     │ • Summarize  │     │             │     │          │
│ • Web       │     │             │     │             │     │          │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
```

## CLI 参考

| 命令 | 说明 |
|------|------|
| `radar init` | 初始化配置文件 |
| `radar run` | 运行完整情报流水线 |
| `radar run -s github` | 仅运行特定数据源 |
| `radar run -v` | 详细模式 |
| `radar doctor` | 检查配置状态 |
| `radar add -r owner/repo` | 添加 GitHub 仓库进行监控 |
| `radar add -k "keyword"` | 添加关键词用于 HN/PH 过滤 |
| `radar add -f <url>` | 添加 RSS 订阅源 |
| `radar set key value` | 设置配置值 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥（必需） |
| `GITHUB_TOKEN` | GitHub 令牌（可选，用于提高速率限制） |

## 许可证

MIT
