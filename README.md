[English](README.md) | [中文](README_CN.md)

# 📡 Radar Agent

**AI-powered competitive intelligence agent** — monitor competitors, track trends, and get actionable insights from GitHub, Hacker News, Product Hunt, RSS feeds, and more.

Radar collects signals from multiple platforms, uses Claude AI to analyze patterns and extract insights, then delivers a structured intelligence digest.

## Features

- 🔍 **Multi-source monitoring** — GitHub repos/orgs/topics, Hacker News, Product Hunt, RSS feeds, web pages
- 🧠 **AI-powered analysis** — Claude filters noise, scores relevance, finds patterns, and generates actionable insights
- 📊 **Structured digests** — Clean Markdown and JSON reports with executive summaries, top stories, trends, and action items
- 🔧 **CLI interface** — Simple commands to configure, run, and manage your intelligence pipeline
- 🌐 **Multi-language** — Digests in Chinese (default) or English
- 🛡️ **Resilient** — Each collector runs independently; errors in one source don't crash the pipeline

## Quick Start

### Install

```bash
# Install with pipx (recommended)
pipx install https://github.com/Jaxz714/radar-agent/archive/main.zip

# Or with pip
pip install https://github.com/Jaxz714/radar-agent/archive/main.zip
```

### Configure

```bash
# Initialize config
radar init

# Set your API key (or use ANTHROPIC_API_KEY env var)
export ANTHROPIC_API_KEY=sk-ant-...

# Add watch targets
radar add -r anthropics/claude-code -r openai/openai-python
radar add -k "AI agent" -k "LLM" -k "Claude"
radar add -o anthropics
radar add -t ai-agent
radar add -f https://blog.anthropic.com/rss.xml
```

Or edit `~/.radar/config.yaml` directly:

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

### Run

```bash
# Run the full pipeline
radar run

# Run specific sources only
radar run -s github -s hackernews

# Verbose output
radar run -v

# Check configuration
radar doctor
```

## Output

Digests are saved to `~/.radar/digests/` in Markdown and/or JSON format.

### Markdown Digest

```markdown
# 📡 Radar Intelligence Digest

> **Date:** 2026-05-30 | **Signals Analyzed:** 42

## 📋 Executive Summary
Today's key developments: Anthropic released Claude 4.5 with...

## 🔥 Top Stories
### 1. 🚀 Claude 4.5 Release
**Score:** 9/10 | **Category:** launch
New model with improved reasoning...

## 📈 Emerging Trends
### MCP ecosystem consolidation
**Evidence:** 3 related signals across GitHub and HN

## ✅ Action Items
- 🔴 [HIGH] Review new Claude 4.5 API changes for integration
```

## Architecture

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

## CLI Reference

| Command | Description |
|---------|-------------|
| `radar init` | Initialize configuration file |
| `radar run` | Run the full intelligence pipeline |
| `radar run -s github` | Run specific source only |
| `radar run -v` | Verbose mode |
| `radar doctor` | Check configuration status |
| `radar add -r owner/repo` | Add GitHub repo to watch |
| `radar add -k "keyword"` | Add keyword for HN/PH filtering |
| `radar add -f <url>` | Add RSS feed |
| `radar set key value` | Set a config value |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key (required) |
| `GITHUB_TOKEN` | GitHub token (optional, for higher rate limits) |

## License

MIT
