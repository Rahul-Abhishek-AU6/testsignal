"""Pure, deterministic path policy for TestSignal."""
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import PurePosixPath

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx"}
DEFAULT_CONFIG = {
    "source_roots": ["src", "lib"],
    "test_roots": ["tests", "test", "__tests__"],
    "exclude": [],
    "strict": False,
}


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    old_path: str | None = None


def normalise(path: str) -> str:
    value = path.replace("\\", "/")
    # Remove only an explicit current-directory prefix.  `lstrip("./")`
    # would also corrupt legitimate tracked dotfiles such as `.config/app.py`.
    while value.startswith("./"):
        value = value[2:]
    if not value or value.startswith("../") or "/../" in value:
        raise ValueError(f"unsafe repository path: {path!r}")
    return value


def excluded(path: str, patterns: list[str]) -> bool:
    return any(fnmatch(path, pattern) or PurePosixPath(path).match(pattern) for pattern in patterns)


def is_test(path: str, test_roots: list[str]) -> bool:
    name = PurePosixPath(path).name
    parts = PurePosixPath(path).parts
    if any(root in parts for root in test_roots):
        return True
    return (name.startswith("test_") and name.endswith(".py")) or name.endswith("_test.py") or any(
        name.endswith(suffix) for suffix in (".test.js", ".test.jsx", ".test.ts", ".test.tsx", ".spec.js", ".spec.jsx", ".spec.ts", ".spec.tsx")
    )


def is_source(path: str, source_roots: list[str]) -> bool:
    parts = PurePosixPath(path).parts
    return PurePosixPath(path).suffix in SOURCE_EXTENSIONS and (not source_roots or any(root in parts for root in source_roots))


def classify(path: str, config: dict) -> str:
    if excluded(path, config["exclude"]):
        return "excluded"
    if is_test(path, config["test_roots"]):
        return "test"
    if is_source(path, config["source_roots"]):
        return "source"
    return "unsupported"


def candidate_tests(path: str, config: dict) -> list[str]:
    pure = PurePosixPath(path)
    suffix = pure.suffix
    stem = pure.stem
    relative = pure
    for root in config["source_roots"]:
        if pure.parts and pure.parts[0] == root:
            relative = PurePosixPath(*pure.parts[1:])
            break
    parent = relative.parent
    candidates: set[str] = set()
    if suffix == ".py":
        for root in config["test_roots"]:
            candidates.add(str(PurePosixPath(root) / parent / f"test_{stem}.py"))
            candidates.add(str(PurePosixPath(root) / parent / f"{stem}_test.py"))
        candidates.add(str(pure.with_name(f"test_{stem}.py")))
    else:
        for root in config["test_roots"]:
            candidates.add(str(PurePosixPath(root) / parent / f"{stem}.test{suffix}"))
            candidates.add(str(PurePosixPath(root) / parent / f"{stem}.spec{suffix}"))
        candidates.add(str(pure.with_name(f"{stem}.test{suffix}")))
        candidates.add(str(pure.with_name(f"{stem}.spec{suffix}")))
    return sorted(candidates)


def build_report(changes: list[Change], base: str, head: str, config: dict) -> dict:
    groups = {"source": [], "test": [], "unsupported": [], "excluded": []}
    active_sources: list[Change] = []
    changed_tests: set[str] = set()
    for change in changes:
        kind = classify(change.path, config)
        groups[kind].append(change.path)
        if kind == "test" and change.status != "D":
            changed_tests.add(change.path)
        if kind == "source" and change.status != "D":
            active_sources.append(change)
    entries = []
    for change in sorted(active_sources, key=lambda item: item.path):
        candidates = candidate_tests(change.path, config)
        matches = sorted(changed_tests.intersection(candidates))
        entries.append({"path": change.path, "status": change.status, "candidate_tests": candidates,
                        "matching_changed_tests": matches, "result": "matched" if matches else "unmatched"})
    for key in groups:
        groups[key].sort()
    return {
        "schema_version": 1,
        "tool": "TestSignal",
        "compared_revisions": {"base": base, "head": head},
        "changed_paths": groups,
        "sources": entries,
        "unmatched": [entry["path"] for entry in entries if entry["result"] == "unmatched"],
        "exclusions": sorted(groups["excluded"]),
        "disclaimer": "Heuristic filename/path signal only; it does not prove test quality, coverage, or correctness.",
    }


def render_text(report: dict) -> str:
    lines = ["TestSignal test-impact receipt", f"Compared: {report['compared_revisions']['base']}..{report['compared_revisions']['head']}", ""]
    if not report["sources"]:
        lines.append("No supported, in-scope source changes.")
    for item in report["sources"]:
        label = "MATCHED" if item["result"] == "matched" else "UNMATCHED"
        lines.append(f"{label}: {item['path']} ({item['status']})")
        if item["matching_changed_tests"]:
            lines.append("  changed tests: " + ", ".join(item["matching_changed_tests"]))
        else:
            lines.append("  candidates: " + ", ".join(item["candidate_tests"]))
    if report["exclusions"]:
        lines.append("Excluded: " + ", ".join(report["exclusions"]))
    if report["changed_paths"]["unsupported"]:
        lines.append("Unsupported: " + ", ".join(report["changed_paths"]["unsupported"]))
    lines.extend(["", report["disclaimer"]])
    return "\n".join(lines) + "\n"
