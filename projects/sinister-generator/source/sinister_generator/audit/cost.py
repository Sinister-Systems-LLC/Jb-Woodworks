"""Cost ledger — append-only markdown rows in memory/cost-ledger.md."""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import json
import pathlib
import time
from typing import Optional, Union

PathLike = Union[str, pathlib.Path]

PROJECT_ROOT = pathlib.Path(r"D:\Sinister Sanctum\projects\sinister-generator")
LEDGER_PATH = PROJECT_ROOT / "memory" / "cost-ledger.md"
MODELS_JSON = PROJECT_ROOT / "config" / "models.json"

_LEDGER_HEADER = """# Sinister Generator — cost ledger

> Author: RKOJ-ELENO :: 2026-05-23
>
> Append-only. Every generation appends one row. Use the verdict column to track
> kept-vs-rejected ratio per project. Cost figures are estimates from
> `config/models.json`; verify against the Google AI Studio billing dashboard.

| UTC | project | model | image_bytes | cost_usd | output | verdict | prompt_excerpt |
|---|---|---|---|---|---|---|---|
"""


def cost_for_model(model_id: str) -> Optional[float]:
    if not MODELS_JSON.exists():
        return None
    try:
        data = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for m in data.get("models", []):
        if m.get("id") == model_id:
            return m.get("approx_cost_per_image_usd")
    return None


def append_cost_row(
    output_path: PathLike,
    model: str,
    image_bytes: int,
    project: str,
    prompt_excerpt: str = "",
    cost_usd: Optional[float] = None,
    verdict: str = "pending",
) -> pathlib.Path:
    """Append one row to the cost ledger. Creates the file with header if missing.

    verdict: "pending" | "kept" | "rejected" | "iterating"
    """
    if cost_usd is None:
        cost_usd = cost_for_model(model) or 0.0

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LEDGER_PATH.exists():
        LEDGER_PATH.write_text(_LEDGER_HEADER, encoding="utf-8")

    utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    excerpt = (prompt_excerpt or "").replace("|", "/").replace("\n", " ")
    if len(excerpt) > 80:
        excerpt = excerpt[:77] + "..."
    out_str = str(output_path).replace("|", "/")

    row = f"| {utc} | {project} | {model} | {image_bytes} | ${cost_usd:.4f} | `{out_str}` | {verdict} | {excerpt} |\n"
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(row)
    return LEDGER_PATH
