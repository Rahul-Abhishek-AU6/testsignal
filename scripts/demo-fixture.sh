#!/bin/sh
# Create a disposable repository and run the exact command shown in the demo.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
cd "$fixture"
git init -q
git config user.email demo@example.invalid
git config user.name Demo
mkdir -p src tests
printf 'def parse(): return 1\n' > src/parser.py
printf 'def format_value(): return 1\n' > src/formatter.py
printf 'def test_parse(): assert True\n' > tests/test_parser.py
git add . && git commit -qm base
printf 'def parse(): return 2\n' > src/parser.py
printf 'def format_value(): return 2\n' > src/formatter.py
printf 'def test_parse(): assert 2 == 2\n' > tests/test_parser.py
git add . && git commit -qm change
PYTHONPATH="$root/src" python3 -m testsignal --base HEAD~1 --head HEAD
