"""JSON digest formatter."""

import json
from datetime import datetime
from pathlib import Path


def render_json(digest: dict) -> str:
    """Render digest as formatted JSON."""
    # Remove internal fields
    output = {k: v for k, v in digest.items() if not k.startswith("_")}
    output["generated_at"] = datetime.now().isoformat()
    return json.dumps(output, ensure_ascii=False, indent=2)


def save_json(digest: dict, output_dir: Path, date: str | None = None) -> Path:
    """Save a JSON digest to file."""
    date = date or datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"radar-{date}.json"
    content = render_json(digest)
    filepath.write_text(content, encoding="utf-8")
    return filepath
