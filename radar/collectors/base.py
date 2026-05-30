"""Base collector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Signal:
    """A single intelligence signal collected from a source."""

    source: str  # e.g., "github", "hackernews"
    title: str
    url: str
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)
    relevance_score: float = 0.0  # 0-1, set by analyzer

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "metadata": self.metadata,
            "collected_at": self.collected_at.isoformat(),
            "relevance_score": self.relevance_score,
        }


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    name: str = "base"
    description: str = "Base collector"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    @abstractmethod
    async def collect(self) -> list[Signal]:
        """Collect signals from this source. Must be implemented by subclasses."""
        ...

    async def safe_collect(self) -> list[Signal]:
        """Collect with error handling — never crashes the pipeline."""
        try:
            return await self.collect()
        except Exception as e:
            return [
                Signal(
                    source=self.name,
                    title=f"⚠️ Collection Error",
                    url="",
                    summary=f"Failed to collect from {self.name}: {e}",
                )
            ]
