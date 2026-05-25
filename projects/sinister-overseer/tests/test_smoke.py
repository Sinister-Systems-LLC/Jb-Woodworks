# Author: RKOJ-ELENO :: 2026-05-24
"""Smoke tests for Sinister Overseer P0 scaffold.

3 tests:
  1. Package + version constant import correctly.
  2. Adapter registry contains all 5 expected adapters with the right keys.
  3. CLI parser builds + handles --help / status / list without errors.
"""

import json
import sys
from pathlib import Path

# Allow running pytest without installing the package
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_package_imports():
    import overseer
    assert hasattr(overseer, "__version__")
    assert overseer.__version__ == "0.0.1"
    assert overseer.__author__ == "RKOJ-ELENO"


def test_adapter_registry_loads():
    from overseer.adapters import REGISTRY, get_adapter
    expected_keys = {
        "sinister-chatbot",
        "eve-compliance",
        "sinister-sleight",
        "sinister-panel",
        "__generic__",
    }
    assert expected_keys.issubset(REGISTRY.keys()), (
        f"missing adapters: {expected_keys - REGISTRY.keys()}"
    )
    # Unknown project_key falls back to GenericAdapter
    fallback = get_adapter("nonexistent-project-key")
    assert fallback.PROJECT_KEY == "__generic__"


def test_cli_parses_and_lists_attachments():
    from overseer.__main__ import build_parser, main
    parser = build_parser()
    # parse smoke
    args = parser.parse_args(["list"])
    assert args.command == "list"
    args = parser.parse_args(["attach", "--project", "sinister-sleight"])
    assert args.command == "attach" and args.project == "sinister-sleight"
    # main returns 0 for version + list
    assert main(["version"]) == 0
    assert main(["list"]) == 0


def test_attached_projects_config_pre_attached_three_prepared():
    """Per MISSION.md: 3 pre-attached lanes ship in status=`prepared`, NOT active."""
    cfg = Path(__file__).resolve().parent.parent / "config" / "attached-projects.json"
    assert cfg.exists(), "config/attached-projects.json must exist at P0"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    attachments = data.get("attachments", [])
    keys = {a["project_key"] for a in attachments}
    assert {"eve-compliance", "sinister-chatbot", "sinister-sleight"}.issubset(keys), (
        f"missing pre-attached: {keys}"
    )
    for a in attachments:
        if a["project_key"] in {"eve-compliance", "sinister-chatbot", "sinister-sleight"}:
            assert a["status"] == "prepared", (
                f"{a['project_key']} must be 'prepared' at P0, got {a['status']}"
            )
