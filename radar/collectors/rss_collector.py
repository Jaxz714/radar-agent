"""RSS/Atom feed collector."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import feedparser
import httpx

from radar.collectors.base import BaseCollector, Signal


class RSSCollector(BaseCollector):
    """Collects signals from RSS/Atom feeds."""

    name = "rss"
    description = "RSS/Atom feed monitoring"

    async def collect(self) -> list[Signal]:
        """Collect signals from configured RSS feeds."""
        signals: list[Signal] = []
        feeds = self.config.get("feeds", [])
        keywords = [k.lower() for k in self.config.get("keywords", [])]
        max_age_hours = self.config.get("max_age_hours", 48)

        for feed_url in feeds:
            signals.extend(await self._collect_feed(feed_url, keywords, max_age_hours))

        return signals

    async def _collect_feed(
        self, feed_url: str, keywords: list[str], max_age_hours: int
    ) -> list[Signal]:
        """Collect entries from a single RSS feed."""
        signals = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    feed_url,
                    headers={"User-Agent": "radar-agent/0.1"},
                    follow_redirects=True,
                )
                if resp.status_code != 200:
                    return signals

            feed = feedparser.parse(resp.text)
            cutoff = datetime.now() - timedelta(hours=max_age_hours)

            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))[:300]
                published = entry.get("published_parsed") or entry.get("updated_parsed")

                # Check age
                if published:
                    pub_date = datetime(*published[:6])
                    if pub_date < cutoff:
                        continue

                # Check keywords
                text_lower = (title + " " + summary).lower()
                matched = [k for k in keywords if k in text_lower] if keywords else []

                if keywords and not matched:
                    continue

                signals.append(
                    Signal(
                        source="rss",
                        title=f"📡 {title}",
                        url=link,
                        summary=summary,
                        metadata={
                            "feed": feed_url,
                            "feed_title": feed.feed.get("title", feed_url),
                            "matched_keywords": matched,
                        },
                    )
                )

        except Exception as e:
            signals.append(
                Signal(
                    source="rss",
                    title=f"⚠️ RSS Error: {feed_url}",
                    url=feed_url,
                    summary=str(e),
                )
            )

        return signals
