"""Product Hunt collector — monitors trending AI products."""

import re
from typing import Any

import httpx

from radar.collectors.base import BaseCollector, Signal


class ProductHuntCollector(BaseCollector):
    """Collects intelligence from Product Hunt."""

    name = "producthunt"
    description = "Product Hunt trending products and launches"

    async def collect(self) -> list[Signal]:
        """Collect signals from Product Hunt."""
        signals: list[Signal] = []
        keywords = [k.lower() for k in self.config.get("keywords", ["ai", "agent", "automation"])]

        async with httpx.AsyncClient(timeout=30) as client:
            # Use Jina Reader to get PH content
            try:
                resp = await client.get(
                    "https://r.jina.ai/https://www.producthunt.com",
                    headers={"User-Agent": "radar-agent/0.1"},
                    follow_redirects=True,
                )
                if resp.status_code == 200:
                    text = resp.text
                    # Extract product blocks from the rendered content
                    # PH pages have structured product listings
                    lines = text.split("\n")
                    current_product = {}
                    products = []

                    for line in lines:
                        line = line.strip()
                        if not line:
                            if current_product.get("name"):
                                products.append(current_product)
                                current_product = {}
                            continue

                        # Try to capture product names (typically bold/heading)
                        if line.startswith("#") or line.startswith("**"):
                            name = line.lstrip("#").strip("*").strip()
                            if name and len(name) < 100:
                                current_product["name"] = name

                    if current_product.get("name"):
                        products.append(current_product)

                    # Create signals from found products
                    for product in products[:15]:
                        name = product.get("name", "")
                        if not name:
                            continue

                        # Check keyword relevance
                        name_lower = name.lower()
                        matched = [k for k in keywords if k in name_lower] if keywords else True

                        if keywords and not matched:
                            continue

                        signals.append(
                            Signal(
                                source="producthunt",
                                title=f"🚀 {name}",
                                url="https://www.producthunt.com",
                                summary=f"Product Hunt launch"
                                + (f" | Keywords: {', '.join(matched)}" if isinstance(matched, list) and matched else ""),
                                metadata={"type": "launch", "matched_keywords": matched if isinstance(matched, list) else []},
                            )
                        )

            except Exception as e:
                signals.append(
                    Signal(
                        source="producthunt",
                        title="⚠️ Product Hunt collection error",
                        url="",
                        summary=str(e),
                    )
                )

        return signals
