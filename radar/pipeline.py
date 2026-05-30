"""Main pipeline — orchestrates collection, analysis, and output."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from radar.analyzers.engine import AnalysisEngine
from radar.collectors import ALL_COLLECTORS
from radar.collectors.base import Signal
from radar.config import Config
from radar.outputs.json_out import save_json
from radar.outputs.markdown import save_markdown

console = Console()


class Pipeline:
    """Orchestrates the full Radar intelligence pipeline."""

    def __init__(self, config: Config):
        self.config = config
        self.engine = AnalysisEngine(
            api_key=config.api_key,
            model=config.get("llm.model", "claude-sonnet-4-6"),
        )

    async def run(self, sources: list[str] | None = None, verbose: bool = False) -> dict[str, Any]:
        """Run the full pipeline: collect → analyze → output.

        Args:
            sources: Specific sources to run, or None for all configured.
            verbose: Print progress details.

        Returns:
            The intelligence digest.
        """
        # Step 1: Collect signals
        console.print("\n[bold cyan]📡 Radar Agent — Collecting Intelligence[/bold cyan]\n")
        signals = await self._collect(sources, verbose)

        if not signals:
            console.print("[yellow]⚠️ No signals collected. Check your configuration.[/yellow]")
            return {}

        console.print(f"\n[green]✅ Collected {len(signals)} signals[/green]\n")

        # Step 2: Analyze
        console.print("[bold cyan]🧠 Analyzing signals...[/bold cyan]\n")

        watch_targets = []
        watch = self.config.get("watch", {})
        watch_targets.extend(watch.get("github_repos", []))
        watch_targets.extend(watch.get("github_orgs", []))
        watch_targets.extend(watch.get("hackernews_keywords", []))

        digest = await self.engine.analyze(
            signals=signals,
            watch_targets=watch_targets,
            language=self.config.get("digest.language", "zh"),
        )

        # Step 3: Output
        fmt = self.config.get("digest.format", "markdown")
        output_dir = self.config.output_dir
        date = datetime.now().strftime("%Y-%m-%d")

        if fmt in ("markdown", "both"):
            md_path = save_markdown(digest, output_dir, date)
            console.print(f"[green]📄 Markdown digest saved: {md_path}[/green]")

        if fmt in ("json", "both"):
            json_path = save_json(digest, output_dir, date)
            console.print(f"[green]📦 JSON digest saved: {json_path}[/green]")

        # Print summary to console
        self._print_summary(digest)

        return digest

    async def _collect(self, sources: list[str] | None, verbose: bool) -> list[Signal]:
        """Run all configured collectors."""
        all_signals: list[Signal] = []
        watch = self.config.get("watch", {})

        collector_configs = {
            "github": {
                "repos": watch.get("github_repos", []),
                "orgs": watch.get("github_orgs", []),
                "topics": watch.get("github_topics", []),
            },
            "hackernews": {
                "keywords": watch.get("hackernews_keywords", []),
                "limit": 30,
            },
            "producthunt": {
                "keywords": watch.get("producthunt_categories", ["ai", "agent"]),
            },
            "rss": {
                "feeds": watch.get("rss_feeds", []),
                "keywords": watch.get("hackernews_keywords", []),  # Reuse keywords
            },
            "web": {
                "pages": watch.get("web_pages", []),
            },
        }

        # Determine which collectors to run
        active_sources = sources or list(collector_configs.keys())

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for source_name in active_sources:
                if source_name not in ALL_COLLECTORS:
                    console.print(f"[yellow]⚠️ Unknown source: {source_name}[/yellow]")
                    continue

                collector_cls = ALL_COLLECTORS[source_name]
                collector_config = collector_configs.get(source_name, {})

                # Skip if no config for this source (except always-on sources)
                if source_name in ("hackernews", "producthunt") and not collector_config.get("keywords"):
                    collector_config["keywords"] = []

                collector = collector_cls(config=collector_config)

                task = progress.add_task(f"Collecting from {source_name}...", total=None)
                signals = await collector.safe_collect()
                progress.update(task, completed=True, description=f"✅ {source_name}: {len(signals)} signals")

                all_signals.extend(signals)

                if verbose:
                    for s in signals:
                        console.print(f"  • {s.title}")

        return all_signals

    def _print_summary(self, digest: dict) -> None:
        """Print a rich summary to console."""
        summary = digest.get("executive_summary", "No summary")
        stories = digest.get("top_stories", [])
        trends = digest.get("emerging_trends", [])
        actions = digest.get("action_items", [])

        console.print("\n")
        console.print(Panel(summary, title="📋 Executive Summary", border_style="cyan"))

        if stories:
            console.print("\n[bold]🔥 Top Stories:[/bold]")
            for s in stories[:3]:
                score = s.get("score", "?")
                console.print(f"  [{score}/10] {s.get('title', '')}")
                console.print(f"         {s.get('significance', '')}")

        if trends:
            console.print("\n[bold]📈 Trends:[/bold]")
            for t in trends:
                console.print(f"  • {t.get('trend', '')}")

        if actions:
            console.print("\n[bold]✅ Actions:[/bold]")
            for a in actions[:3]:
                priority = a.get("priority", "medium")
                color = {"high": "red", "medium": "yellow", "low": "green"}.get(priority, "white")
                console.print(f"  [{color}][{priority.upper()}][/{color}] {a.get('action', '')}")

        console.print()
