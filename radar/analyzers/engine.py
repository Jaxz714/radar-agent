"""AI-powered analysis engine for Radar Agent."""

import json
from datetime import datetime
from typing import Any

import anthropic

from radar.collectors.base import Signal

SYSTEM_PROMPT = """You are Radar, an elite competitive intelligence analyst.

Your job is to analyze raw signals collected from various platforms (GitHub, Hacker News, Product Hunt, RSS feeds, web pages) and produce structured, actionable intelligence.

You must:
1. FILTER — Remove noise, duplicates, and low-value signals.
2. CLASSIFY — Tag each signal by type: launch, update, trend, controversy, opportunity, threat, insight.
3. SCORE — Rate relevance from 1-10 based on: novelty, impact, urgency, and strategic value.
4. CONNECT — Find patterns across signals. What stories are emerging? What trends are forming?
5. SUMMARIZE — Produce a concise, actionable intelligence brief.

Always respond in the specified JSON format. Be opinionated — your job is to separate signal from noise.
"""

DIGEST_PROMPT = """Analyze these {count} signals collected on {date}.

Watch targets: {targets}

{signals_json}

Respond with a JSON object in this exact format:
{{
  "executive_summary": "2-3 sentence overview of today's most important developments",
  "top_stories": [
    {{
      "title": "story title",
      "significance": "why this matters",
      "signals": ["related signal titles"],
      "score": 8,
      "category": "launch|update|trend|opportunity|threat|insight"
    }}
  ],
  "emerging_trends": [
    {{
      "trend": "trend description",
      "evidence": ["supporting signal titles"],
      "implication": "what this means"
    }}
  ],
  "action_items": [
    {{
      "action": "specific recommended action",
      "priority": "high|medium|low",
      "reason": "why"
    }}
  ],
  "signals_by_source": {{
    "github": {{"count": 0, "highlights": []}},
    "hackernews": {{"count": 0, "highlights": []}},
    "producthunt": {{"count": 0, "highlights": []}},
    "rss": {{"count": 0, "highlights": []}},
    "web": {{"count": 0, "highlights": []}}
  }},
  "noise_filtered": "brief description of what was filtered out and why"
}}

Rules:
- top_stories: max 5, sorted by score descending
- emerging_trends: max 3
- action_items: max 5
- scores range 1-10
- Be specific and actionable, not vague
- If you detect a pattern across multiple sources, highlight it as a trend
"""


class AnalysisEngine:
    """AI-powered analysis engine using Claude."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    async def analyze(
        self,
        signals: list[Signal],
        watch_targets: list[str] | None = None,
        language: str = "zh",
    ) -> dict[str, Any]:
        """Analyze collected signals and produce an intelligence digest."""
        if not signals:
            return {
                "executive_summary": "No signals collected. Check your configuration.",
                "top_stories": [],
                "emerging_trends": [],
                "action_items": [],
                "signals_by_source": {},
                "noise_filtered": "N/A",
            }

        # Prepare signals for analysis
        signals_data = [s.to_dict() for s in signals]

        # Build the prompt
        prompt = DIGEST_PROMPT.format(
            count=len(signals),
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            targets=", ".join(watch_targets) if watch_targets else "General monitoring",
            signals_json=json.dumps(signals_data, ensure_ascii=False, indent=2),
        )

        if language == "zh":
            prompt += "\n\nIMPORTANT: Write all text fields (executive_summary, significance, implication, action, reason, etc.) in Chinese (简体中文). Keep technical terms, product names, and company names in English."

        # Call Claude
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text

            # Try to parse JSON from response
            result = self._parse_json(response_text)
            result["_raw_signal_count"] = len(signals)
            result["_model"] = self.model
            result["_timestamp"] = datetime.now().isoformat()
            return result

        except anthropic.APIError as e:
            return {
                "executive_summary": f"Analysis failed: API error — {e}",
                "top_stories": [],
                "emerging_trends": [],
                "action_items": [{"action": "Check your API key and quota", "priority": "high", "reason": str(e)}],
                "signals_by_source": {},
                "noise_filtered": "N/A",
                "_error": str(e),
            }
        except Exception as e:
            return {
                "executive_summary": f"Analysis failed: {e}",
                "top_stories": [],
                "emerging_trends": [],
                "action_items": [],
                "signals_by_source": {},
                "noise_filtered": "N/A",
                "_error": str(e),
            }

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        import re
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding first { to last }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        return {
            "executive_summary": text[:500],
            "top_stories": [],
            "emerging_trends": [],
            "action_items": [],
            "signals_by_source": {},
            "noise_filtered": "N/A",
            "_parse_error": True,
        }
