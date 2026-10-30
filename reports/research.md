# Research: change-aware test review for agent-authored patches

Researched on 2026-10-30 (IST). This is a product-selection report, not a
claim that static analysis can prove behavioural correctness.

## Decision

Build **TestSignal**: a zero-dependency, local CLI that inspects a Git diff,
maps modified source files to likely colocated tests using transparent naming
rules, and produces a reviewable test-impact report. It should fail a CI gate
only when the configured policy says a changed source file needs a matching
test change and none is present. It will also print the exact candidate test
files and clearly label uncertainty.

The narrow job is *not* to run tests, measure coverage, or ask an LLM whether
a patch is correct. It is to make a common review question cheap and explicit:
“this production module changed—what test moved with it, or why is none
expected?”

## Evidence and trend signals

1. GitHub’s Octoverse 2026 reports that by September 2026, more than 40% of
   GitHub pull requests began with an agent’s first draft (110 million that
   month, roughly six times March’s volume). Agent-started PRs also changed
   multiple files more often (87% versus 79%). That increases the number of
   diffs reviewers must validate and makes a small, deterministic pre-review
   signal valuable. [GitHub Octoverse, published 2026-10-28](https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/).

2. The Stack Overflow Developer Survey 2026 records 73% daily use among users
   of coding assistants/agents (8,403 respondents in the survey’s data view).
   This is a mainstream workflow rather than an edge case.
   [Stack Overflow, 2026 data](https://survey.stackoverflow.co/2026/ai/data/ai-freq).

3. In the same survey’s task-delegation data, 72.9% had delegated code writing,
   50.6% test writing/maintenance, and 44.9% code/PR/technical-change review
   to AI in the previous 30 days. The workflow needs tools that give humans
   auditable signals around tests and review—not another opaque code generator.
   [Stack Overflow, 2026 knowledge data](https://survey.stackoverflow.co/2026/knowledge/data).

4. GitLab’s 2026 Global DevSecOps Report frames an “AI Efficiency Paradox” and
   reports a mix of AI-generated, freshly written, and copied code. That mixed
   provenance reinforces the value of repository-local, provider-neutral
   checks. [GitLab report landing page, accessed 2026-10-30](https://about.gitlab.com/resources/developer-survey/).

## Intended user and urgency

The primary user is a maintainer or reviewer of a small Python/JavaScript
repository that accepts AI-assisted changes and wants a lightweight check in a
local pre-review routine or CI. Their immediate pain is time lost tracing a
changed module to relevant tests and discovering late that no test changed.
The result must be easy to audit: plain text/JSON, deterministic mappings, no
network calls, no repository upload, and no hidden scoring.

## Candidate comparison

| Candidate | Why not selected now |
| --- | --- |
| LLM PR reviewer | Needs credentials/model access, may leak code, and has non-deterministic claims. |
| Full coverage-diff analyzer | Useful but language/runtime/coverage-tool dependent; too broad for a reliable first local release. |
| Generic agent-diff policy checker | Already overlaps the prior Scopeguard project and does not answer the test-impact question. |
| Secret scanner | Valuable but mature ecosystem and not distinct from existing local scanners. |
| **TestSignal** | Narrow, current, auditable, and feasible with Python standard library plus Git. |

## Local/free feasibility

Implement in Python 3 standard library, using `git diff --name-status` and
path/name heuristics only. No packages, API key, account, telemetry, or network
connection are required. Support an optional checked-in `.testsignal.json`
policy for source/test roots, filename conventions, excluded paths, and a
strict exit status. Tests can use temporary Git repositories and fixtures.

## Constraints and risks

- Name/path matching is heuristic; it cannot prove a test is adequate. Reports
  must state that conclusion explicitly.
- Monorepos and generated code need configuration/exclusion support.
- The first release should target Python and JS/TS conventions only; unknown
  extensions are reported but not failed by default.
- A test change can be superficial. This tool makes review evidence visible;
  it does not replace execution or human review.

## Acceptance direction for planning

Given a fixture Git repository, TestSignal should identify changed supported
source files; recognize matching changed test files; flag source changes with
no matching test change; emit stable JSON; honour exclusions; and return a
non-zero status in strict mode when an unmatched supported source change is
found. The build must include a runnable fixture/demo and automated tests.
