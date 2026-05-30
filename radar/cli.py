"""CLI interface for Radar Agent."""

import asyncio

import click
from rich.console import Console

from radar.config import Config

console = Console()


@click.group()
@click.option("--config", "-c", "config_path", default=None, help="Path to config file")
@click.pass_context
def main(ctx, config_path):
    """📡 Radar Agent — AI-powered competitive intelligence.

    Monitor competitors, track trends, and get actionable insights
    from GitHub, Hacker News, Product Hunt, RSS feeds, and more.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


@main.command()
@click.pass_context
def init(ctx):
    """Initialize Radar configuration."""
    config_path = ctx.obj.get("config_path")
    config = Config.init_config(config_path)
    console.print(f"[green]✅ Configuration created at {config.path}[/green]")
    console.print(f"\nEdit it to add your watch targets:")
    console.print(f"  [cyan]{config.path}[/cyan]")
    console.print(f"\nThen run:")
    console.print(f"  [cyan]radar run[/cyan]")


@main.command()
@click.option("--source", "-s", multiple=True, help="Specific source(s) to collect from")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def run(ctx, source, verbose):
    """Run the intelligence pipeline — collect, analyze, output."""
    config = _load_config(ctx)

    from radar.pipeline import Pipeline

    pipeline = Pipeline(config)
    sources = list(source) if source else None
    asyncio.run(pipeline.run(sources=sources, verbose=verbose))


@main.command()
@click.pass_context
def doctor(ctx):
    """Check configuration and connectivity."""
    config = _load_config(ctx)
    console.print("\n[bold cyan]📡 Radar Configuration Status[/bold cyan]\n")

    # Check API key
    try:
        key = config.api_key
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        console.print(f"  ✅ API Key: {masked}")
    except ValueError:
        console.print("  ❌ API Key: Not configured")
        console.print("     Set ANTHROPIC_API_KEY env var or edit ~/.radar/config.yaml")

    # Check model
    console.print(f"  📦 Model: {config.get('llm.model', 'N/A')}")

    # Check watch targets
    watch = config.get("watch", {})
    total_targets = 0
    for key, items in watch.items():
        if items:
            total_targets += len(items)
            console.print(f"  ✅ {key}: {len(items)} target(s)")
        else:
            console.print(f"  ⚪ {key}: none")

    if total_targets == 0:
        console.print("\n  [yellow]⚠️ No watch targets configured![/yellow]")
        console.print(f"  Edit [cyan]{config.path}[/cyan] to add repos, keywords, feeds, etc.")
    else:
        console.print(f"\n  📊 Total watch targets: {total_targets}")

    # Check output dir
    console.print(f"  📁 Output: {config.output_dir}")
    console.print()


@main.command()
@click.argument("key")
@click.argument("value")
@click.pass_context
def set(ctx, key, value):
    """Set a config value. Example: radar set llm.model claude-sonnet-4-20250514"""
    config = _load_config(ctx)
    config.set(key, value)
    config.save()
    console.print(f"[green]✅ Set {key} = {value}[/green]")


@main.command()
@click.option("--repo", "-r", multiple=True, help="GitHub repo (e.g., anthropics/claude)")
@click.option("--org", "-o", multiple=True, help="GitHub org to monitor")
@click.option("--topic", "-t", multiple=True, help="GitHub topic to track")
@click.option("--keyword", "-k", multiple=True, help="Keywords for HN/Product Hunt matching")
@click.option("--feed", "-f", multiple=True, help="RSS feed URL")
@click.pass_context
def add(ctx, repo, org, topic, keyword, feed):
    """Add watch targets to configuration."""
    config = _load_config(ctx)

    if repo:
        existing = config.get("watch.github_repos", [])
        existing.extend(repo)
        config.set("watch.github_repos", list(set(existing)))
        console.print(f"[green]✅ Added GitHub repos: {', '.join(repo)}[/green]")

    if org:
        existing = config.get("watch.github_orgs", [])
        existing.extend(org)
        config.set("watch.github_orgs", list(set(existing)))
        console.print(f"[green]✅ Added GitHub orgs: {', '.join(org)}[/green]")

    if topic:
        existing = config.get("watch.github_topics", [])
        existing.extend(topic)
        config.set("watch.github_topics", list(set(existing)))
        console.print(f"[green]✅ Added GitHub topics: {', '.join(topic)}[/green]")

    if keyword:
        existing_hn = config.get("watch.hackernews_keywords", [])
        existing_hn.extend(keyword)
        config.set("watch.hackernews_keywords", list(set(existing_hn)))
        console.print(f"[green]✅ Added keywords: {', '.join(keyword)}[/green]")

    if feed:
        existing = config.get("watch.rss_feeds", [])
        existing.extend(feed)
        config.set("watch.rss_feeds", list(set(existing)))
        console.print(f"[green]✅ Added RSS feeds: {', '.join(feed)}[/green]")

    config.save()


@main.command()
@click.pass_context
def watch(ctx):
    """Quick health check — same as `radar doctor`."""
    ctx.invoke(doctor)


def _load_config(ctx) -> Config:
    """Load config, creating if needed."""
    config_path = ctx.obj.get("config_path")
    config = Config(config_path)
    return config


if __name__ == "__main__":
    main()
