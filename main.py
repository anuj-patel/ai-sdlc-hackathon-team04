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
    parser.add_argument("--input", help="Path to a transcript, email, or one-liner")
    parser.add_argument("--text", help="Inline messy requirement text")
    parser.add_argument("--context", help="Path to a project document used for validation")
    parser.add_argument("--repo", help="GitHub URL or owner/repo. The README is used for validation")
    args = parser.parse_args()
    project_context = ""
    if args.context:
        project_context = Path(args.context).read_text(encoding="utf-8")
    result = run(_read_input(args), project_context=project_context, repo=args.repo)
    print(json.dumps(result.export_dict(), indent=2))


if __name__ == "__main__":
    main()
