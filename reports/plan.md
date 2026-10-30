# Plan: TestSignal

## Goal and success metric

TestSignal answers one deliberately narrow review question for a Git patch:
which changed Python or JavaScript/TypeScript production modules have a likely
matching test change, and which do not? A maintainer can run one local command
without an account, package install, network request, or code upload and get a
stable text or JSON receipt. Success for v1 is a deterministic report over a
fixture repository that correctly classifies all supported changed files in
the acceptance cases below.

This is a heuristic review signal. It must never claim to prove test quality,
coverage, or behavioural correctness.

## Minimal architecture

```
CLI arguments/config
        |
git diff --name-status <base> [<head>]
        |
normalise changed paths and statuses
        |
classify: source | test | unsupported | excluded
        |
derive transparent candidate test paths
        |
match changed source paths to changed test paths
        |
stable report model  ---> human-readable text
        |                 JSON (--format json)
        +-- strict-policy exit status
```

Implement a Python package under `src/testsignal/` with a thin executable
entry point (`python3 -m testsignal` is sufficient for v1). Keep pure path
classification, candidate generation, matching, and report rendering as
separate standard-library modules/functions so they can be tested without a
Git process. One small Git adapter runs `git diff --name-status` and converts
its output into records.

Default conventions:

- Supported source extensions: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`.
- Tests are paths under `tests/`, `test/`, `__tests__/`, or names matching
  `test_*.py`, `*_test.py`, `*.test.[jt]s[x]`, or `*.spec.[jt]s[x]`.
- Candidate paths are conventional colocated and root-based forms, such as
  `src/widget.py` -> `tests/test_widget.py`, `tests/widget_test.py`, and
  `src/widget.test.ts`; candidates are evidence, not asserted file existence.
- Deleted source files and renamed-away paths are reported, but do not create
  an unmatched-test requirement in v1. Added/modified/renamed-to source paths
  do.

## Configuration and report contract

An optional checked-in `.testsignal.json` accepts only simple local policy:

```json
{
  "source_roots": ["src", "lib"],
  "test_roots": ["tests", "test", "__tests__"],
  "exclude": ["vendor/**", "generated/**"],
  "strict": false
}
```

Missing configuration uses defaults. Malformed configuration must produce a
clear non-zero error rather than silently changing policy. Glob matching must
be implemented with `pathlib`/`fnmatch` from the standard library.

The JSON report contains a schema/version marker, compared revisions, changed
paths grouped by classification, per-supported-source entries (`path`,
`status`, `candidate_tests`, `matching_changed_tests`, `result`), unmatched
paths, exclusions, and a disclaimer. Lists must be sorted for reproducibility.
The text report renders the same evidence in a compact review format. `--strict`
(or config `strict: true`) returns exit code 1 only when unmatched supported
source paths exist; ordinary analysis returns 0. Invalid arguments, invalid
configuration, or Git failures return a distinct usage/runtime non-zero code.

## Local/free dependency inventory

- Python 3.9+ standard library only (`argparse`, `dataclasses`, `json`,
  `pathlib`, `subprocess`, `unittest`, `tempfile`).
- Git, only when inspecting a repository diff.
- No third-party package manager, hosted API, telemetry, account, model, or
  network connection.

## Security and privacy

- Run Git with argument arrays, never a shell command constructed from a path
  or revision.
- Treat Git output and config as untrusted input; validate record shape and
  JSON types, and do not execute content from either.
- Do not read source contents in v1—only diff filenames—so the tool minimises
  exposure and is safe for local/offline use.
- Avoid writing outside the invoked working tree. Reports print to stdout;
  any optional `--output` path must be explicit.

## Build breakdown

1. Create the package, CLI help, data model, and stable exit-code constants.
2. Implement diff parsing for added, modified, deleted, and renamed files.
3. Implement path normalisation, classification, exclusions, and documented
   Python/JS/TS candidate rules.
4. Implement source-to-changed-test matching and text/JSON renderers.
5. Add `.testsignal.json` loading plus `--base`, `--head`, `--format`,
   `--strict`, and `--config` options.
6. Add unit tests for pure functions and integration tests using a temporary
   Git repository and commits.
7. Add README, MIT license, a committed safe fixture, and a truthful terminal
   demo asset generated from that fixture.

## Executable acceptance tests

Run from the project root after implementation:

1. `python3 -m unittest discover -s tests -v` passes all unit and integration
   tests.
2. In the fixture Git repo, changing `src/parser.py` and
   `tests/test_parser.py` yields JSON where `src/parser.py` is `matched` and
   names the changed test.
3. Changing `src/formatter.py` without a test change yields `unmatched`, lists
   deterministic candidates, and exits 0 without strict mode.
4. Re-running case 3 with `--strict` exits 1 and preserves the same JSON
   report content (apart from explicitly documented revision metadata).
5. A changed excluded source path is listed as excluded and does not fail
   strict mode.
6. A changed unsupported extension is reported as unsupported and does not
   fail strict mode.
7. A malformed config and an invalid Git revision fail clearly, with no
   traceback in normal CLI output.
8. The README quick-start command works against the committed fixture, and
   its referenced demo asset depicts that exact command/output.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Path heuristics miss custom layouts | Provide transparent candidate lists and configurable roots/exclusions; never assert completeness. |
| A changed test is weak or unrelated | Document that matching is not quality/coverage proof; test execution remains separate. |
| Rename/status parsing differs across Git versions | Cover standard `--name-status` rename records in integration tests; treat malformed records as errors. |
| Monorepos/generated files create noise | Make exclusions and roots explicit in checked-in config. |
| Strict mode is adopted prematurely | Default it off and fail only supported, in-scope unmatched paths. |

## Build handoff

Implement only this deterministic first release. Do not add LLM analysis,
coverage tooling, test execution, language parsing, remote services, or claims
that the result proves a patch is safe.
