"""Web page collector — monitors specific web pages for changes."""

from typing import Any

import httpx

from radar.collectors.base import BaseCollector, Signal


class WebCollector(BaseCollector):
    """Collects content from specific web pages using Jina Reader."""

    name = "web"
    description = "Web page monitoring via Jina Reader"

    async def collect(self) -> list[Signal]:
        """Collect content from configured web pages."""
        signals: list[Signal] = []
        pages = self.config.get("pages", [])
        keywords = [k.lower() for k in self.config.get("keywords", [])]

        async with httpx.AsyncClient(timeout=60) as client:
            for page in pages:
                signals.extend(await self._collect_page(client, page, keywords))

        return signals

    async def _collect_page(
        self, client: httpx.AsyncClient, page: dict[str, str], keywords: list[str]
    ) -> list[Signal]:
        """Fetch and extract content from a web page."""
        signals = []
        url = page.get("url", "")
        name = page.get("name", url)

        if not url:
            return signals

        try:
            # Use Jina Reader for clean content extraction
            jina_url = f"https://r.jina.ai/{url}"
            resp = await client.get(
                jina_url,
                headers={"User-Agent": "radar-agent/0.1"},
                follow_redirects=True,
            )

            if resp.status_code != 200:
                signals.append(
                    Signal(
                        source="web",
                        title=f"⚠️ Failed to fetch: {name}",
                        url=url,
                        summary=f"HTTP {resp.status_code}",
                    )
                )
                return signals

            content = resp.text[:2000]  # Truncate for analysis

            # Check keywords
            content_lower = content.lower()
            matched = [k for k in keywords if k in content_lower] if keywords else []

            if keywords and not matched:
                return signals

            signals.append(
                Signal(
                    source="web",
                    title=f"🌐 {name}",
                    url=url,
                    summary=content[:500],
                    metadata={
                        "matched_keywords": matched,
                        "content_length": len(resp.text),
                    },
                )
            )

        except Exception as e:
            signals.append(
                Signal(
                    source="web",
                    title=f"⚠️ Web Error: {name}",
                    url=url,
                    summary=str(e),
                )
            )

        return signals
