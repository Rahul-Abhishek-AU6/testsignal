# Publication readiness: TestSignal

Date: 2026-10-30

## Readiness

**Ready for public GitHub publication once externally authorized.** This
stage did not create a remote repository or push any files.

## Checks

- README: present, with purpose, limitations, requirements, quick start,
  local policy, verification commands, and MIT license link.
- License: MIT, present as `LICENSE`.
- Demo: `assets/testsignal-demo.svg` is README-linked and reproducible via
  `scripts/demo-fixture.sh`; QA ran that script successfully.
- Tests: independent QA passed 6/6 tests and a real smoke run; see
  `reports/test.md`.
- Dependencies: Python 3.9+ standard library and Git only. No package lock,
  hosted service, API key, telemetry, or account is required for use.
- Secret scan: no credential material was found. Matches for the word
  "secrets" are documentation/research text only.
- Git: a local repository and source commit are prepared for the eventual
  public push. No remote was added by this stage.

## External release procedure

When the project is expressly authorized for GitHub publication, create an
empty **public** repository named `testsignal` with no auto-generated README,
license, or `.gitignore`, then add its remote and push the existing local
`main` branch. Confirm the public README renders the SVG and verify the
repository URL before any Reddit-post workflow begins.

No Reddit draft or submission was created in this stage.
