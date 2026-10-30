# Showcase report: TestSignal

Date: 2026-10-30

## README review

The README clearly communicates the narrow problem, local/offline operation,
quick start, configuration, verification, and limitations. Its opening
disclaimer correctly avoids claims about coverage, correctness, or safety.

## Truthful visual

`assets/testsignal-demo.svg` is linked directly below the README introduction.
It is a terminal-style rendering of the exact output from:

```sh
./scripts/demo-fixture.sh
```

The script builds a disposable Git fixture, commits a base and change, and
runs the documented TestSignal command. QA reran it on 2026-10-30 and
confirmed the displayed matched/unmatched receipt. The asset is therefore a
reproducible demonstration, not a fabricated product screenshot.

## Public-release gate

Push this README-linked visual with the source before any external promotion.
The project is ready for that step when publication is authorized.
