"""Hacker News collector — monitors top stories and keyword matches."""

import asyncio
from typing import Any

import httpx

from radar.collectors.base import BaseCollector, Signal


class HNCollector(BaseCollector):
    """Collects intelligence from Hacker News."""

    name = "hackernews"
    description = "Hacker News top stories and keyword monitoring"

    HN_API = "https://hacker-news.firebaseio.com/v0"

    async def collect(self) -> list[Signal]:
        """Collect signals from Hacker News."""
        signals: list[Signal] = []
        keywords = [k.lower() for k in self.config.get("keywords", [])]
        limit = self.config.get("limit", 30)

        async with httpx.AsyncClient(timeout=30) as client:
            # Get top stories
            resp = await client.get(f"{self.HN_API}/topstories.json")
            if resp.status_code != 200:
                return signals

            story_ids = resp.json()[:limit]

            # Fetch stories concurrently (with semaphore to avoid rate limiting)
            sem = asyncio.Semaphore(10)

            async def fetch_story(sid: int) -> dict | None:
                async with sem:
                    try:
                        r = await client.get(f"{self.HN_API}/item/{sid}.json")
                        return r.json() if r.status_code == 200 else None
                    except Exception:
                        return None

            stories = await asyncio.gather(*[fetch_story(sid) for sid in story_ids])
            stories = [s for s in stories if s]

            for story in stories:
                title = story.get("title", "")
                score = story.get("score", 0)
                url = story.get("url", f"https://news.ycombinator.com/item?id={story['id']}")
                comments = story.get("descendants", 0)

                # Check keyword relevance
                title_lower = title.lower()
                matched_keywords = [k for k in keywords if k in title_lower] if keywords else []

                if keywords and not matched_keywords:
                    continue  # Skip if keywords specified but none match

                signals.append(
                    Signal(
                        source="hackernews",
                        title=f"📰 {title}",
                        url=url,
                        summary=f"⬆️ {score} points | 💬 {comments} comments"
                        + (f" | Keywords: {', '.join(matched_keywords)}" if matched_keywords else ""),
                        metadata={
                            "score": score,
                            "comments": comments,
                            "hn_url": f"https://news.ycombinator.com/item?id={story['id']}",
                            "matched_keywords": matched_keywords,
                        },
                    )
                )

        # Sort by score
        signals.sort(key=lambda s: s.metadata.get("score", 0), reverse=True)
        return signals
