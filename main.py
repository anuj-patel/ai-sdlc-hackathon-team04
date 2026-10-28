from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.pipeline import run


def _read_input(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.input:
        return Path(args.input).read_text(encoding="utf-8")
    raise SystemExit("Pass --text or --input")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vague requirements → gated tickets")
    parser.add_argument("--input", help="Path to a transcript/email/text file")
    parser.add_argument("--text", help="Inline messy requirement text")
    args = parser.parse_args()
    result = run(_read_input(args))
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
