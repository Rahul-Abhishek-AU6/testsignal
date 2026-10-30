# Independent QA report: TestSignal

Date: 2026-10-30

## Result

**PASS.** TestSignal meets the planned local-only acceptance criteria that are
implemented in this release. It produces deterministic path-based receipts;
it does not claim to execute or validate tests.

## Commands run

From the project root:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
./scripts/demo-fixture.sh
python3 -m py_compile src/testsignal/*.py
```

## Evidence

- The automated suite passed **6/6** tests. It includes pure candidate-path
  and classification tests plus temporary-Git integration coverage for matched
  and unmatched files, exclusions, unsupported files, strict mode, and bad
  revisions.
- The real disposable-Git smoke run reported `src/parser.py` as **MATCHED**
  by `tests/test_parser.py` and `src/formatter.py` as **UNMATCHED**, with the
  documented deterministic candidates.
- Additional QA probes confirmed strict mode exits `1` while emitting valid
  JSON for an unmatched source; invalid revisions and malformed config exit
  `2` with a `testsignal: error:` message and no traceback.
- `python3 -m py_compile` completed successfully.
- The README-linked `assets/testsignal-demo.svg` is truthful: it depicts the
  exact command and material output from `scripts/demo-fixture.sh`, which
  recreates its own disposable fixture repository.

## QA fix incorporated

QA identified that `normalise()` previously used `lstrip("./")`, which could
alter a valid dot-prefixed tracked path. The builder replaced it with exact
leading-`./` handling and added a regression test for `.config/app.py`. The
full suite was rerun after that fix.

## Remaining limitations

Candidate mappings are intentionally heuristic. Custom layouts, monorepos,
renames, generated source, and weak/unrelated tests still need human review
or local `.testsignal.json` policy.
