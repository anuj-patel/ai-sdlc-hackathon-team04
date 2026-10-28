from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline import run

ROOT = Path(__file__).resolve().parent


def evaluate_fixture(path: Path) -> dict:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    result = run(fixture["input"])
    expected = fixture["expected"]
    ready_n = len(result.tickets)
    rejected_n = len(result.rejected)
    clarify_n = len(result.needs_clarification)
    checks = {
        "min_ready": ready_n >= expected.get("min_ready", 0),
        "max_ready": ready_n <= expected.get("max_ready", 99),
        "min_rejected": rejected_n >= expected.get("min_rejected", 0),
        "min_clarify": clarify_n >= expected.get("min_clarify", 0),
    }
    return {
        "fixture": path.name,
        "pass": all(checks.values()),
        "got": {"ready": ready_n, "rejected": rejected_n, "clarify": clarify_n},
        "expected": expected,
        "checks": checks,
        "rejected_reasons": [g.reasons for g in result.rejected],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default=str(ROOT / "fixtures"))
    args = parser.parse_args()
    paths = sorted(Path(args.fixtures).glob("*.json"))
    if not paths:
        raise SystemExit(f"No fixtures in {args.fixtures}")
    reports = [evaluate_fixture(path) for path in paths]
    print(json.dumps(reports, indent=2))
    failed = [r for r in reports if not r["pass"]]
    if failed:
        raise SystemExit(f"{len(failed)} fixture(s) failed")


if __name__ == "__main__":
    main()
