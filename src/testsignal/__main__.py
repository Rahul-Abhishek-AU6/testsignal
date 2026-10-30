from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .core import Change, DEFAULT_CONFIG, build_report, normalise, render_text


def load_config(filename: str | None) -> dict:
    config = {key: list(value) if isinstance(value, list) else value for key, value in DEFAULT_CONFIG.items()}
    path = Path(filename or ".testsignal.json")
    if not path.exists():
        return config
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid config {path}: {error}") from error
    if not isinstance(raw, dict) or set(raw) - set(DEFAULT_CONFIG):
        raise ValueError("invalid config: expected only source_roots, test_roots, exclude, strict")
    for key in ("source_roots", "test_roots", "exclude"):
        if key in raw and (not isinstance(raw[key], list) or not all(isinstance(value, str) for value in raw[key])):
            raise ValueError(f"invalid config: {key} must be a list of strings")
    if "strict" in raw and not isinstance(raw["strict"], bool):
        raise ValueError("invalid config: strict must be boolean")
    config.update(raw)
    return config


def git_changes(base: str, head: str) -> list[Change]:
    result = subprocess.run(["git", "diff", "--name-status", "-M", base, head], text=True, capture_output=True)
    if result.returncode:
        detail = result.stderr.strip() or "git diff failed"
        raise RuntimeError(detail)
    changes = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            raise RuntimeError(f"unparseable git diff record: {line!r}")
        status = fields[0][0]
        if status in {"R", "C"}:
            if len(fields) != 3:
                raise RuntimeError(f"unparseable rename record: {line!r}")
            changes.append(Change(status, normalise(fields[2]), normalise(fields[1])))
        elif status in {"A", "M", "D", "T"}:
            changes.append(Change(status, normalise(fields[1])))
        else:
            raise RuntimeError(f"unsupported git status: {fields[0]!r}")
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report likely changed tests for a Git diff; never a proof of correctness.")
    parser.add_argument("--base", default="HEAD~1", help="base Git revision (default: HEAD~1)")
    parser.add_argument("--head", default="HEAD", help="head Git revision (default: HEAD)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="exit 1 for unmatched supported source paths")
    parser.add_argument("--config", help="path to .testsignal.json")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        report = build_report(git_changes(args.base, args.head), args.base, args.head, config)
    except (ValueError, RuntimeError) as error:
        print(f"testsignal: error: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")
    return 1 if (args.strict or config["strict"]) and report["unmatched"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
