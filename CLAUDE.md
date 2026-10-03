# Working agreements

How to work in this repository.

| Fact | Value |
|---|---|
| Stack | Python 3.12+ |
| Dependencies | Poetry (lock committed) |
| Lint / format | ruff |
| Tests | pytest, pytest-django, Playwright (tests/ fast, tests_e2e/ browser) |
| Spec workflow | OpenSpec (openspec/) |
| Everything else | English |

## Language

- *English* in code, identifiers, database tables and columns, comments, commit messages, branch names, documentation and specs.
- Plain, simple English - the way developers talk. Short sentences, no marketing tone, no filler.
- Comments are short and say *why*, not what the next line already shows. No commented-out code.
- *User-facing strings stay in the product language* and live in templates, forms and messages - never in identifiers or logic.
- Talk to the user in their language; write files in English.

## Never show that an assistant was involved

No Co-Authored-By, no "generated with", no mention of AI, assistants or agents in any file, comment, document or commit message.

## Spec-driven work (OpenSpec)

- Flow: *explore → propose → review → apply → archive*. Discuss first; *create a change only when the user orders it*, and never quietly push scope to "later".
- A change holds proposal.md (why, what, non-goals, assumptions to confirm), spec deltas, design.md (decisions with alternatives and Mermaid diagrams) and tasks.md.
- Specs describe *behaviour*, not implementation: SHALL`/MUST`, one scenario per case with WHEN`/THEN`, every scenario testable.
- MODIFIED requirements carry the full new text. Tooling-, test- or docs-only changes set skip_specs: true instead of inventing requirements.
- tasks.md groups tasks so that *one group is one commit*, each with its own verification step.
- One branch per change; archive (which syncs the main specs) before merging into main.
- Record every assumption you had to make under "Assumptions to confirm at review" rather than deciding silently.

## Working with the user

- Settle open decisions *before* implementation; then implement the agreed scope without interrupting with questions.
- Recommend one option with its trade-offs instead of listing everything; say plainly when something is a guess.
- Hands-on guidance (setting up a machine, manual checks): *one short step per message*, then wait for the result.
- Report outcomes honestly: failing tests with their output, skipped steps, known gaps.

## Dependencies and configuration

- Poetry for everything; development tools in the dev group; the lock file is committed. Applications set package-mode = false.
- Settings read the environment; .env is local and ignored, .env.example is committed.
- Fail fast on a missing secret when debug is off. Never commit secrets, databases or generated output.

## Code

- Business rules live in services and small pure helpers; views stay thin and templates hold no logic.
- Validate in the model or service *and* back it with database constraints (uniqueness, check constraints) so paths that bypass the application cannot break an invariant.
- Concurrency: atomic conditional UPDATEs instead of read-modify-write; make repeated submissions idempotent.
- Migrations are additive and reversible; data migrations are idempotent and tested forward and backward.
- Stay database-agnostic unless the target database is fixed forever.
- Prefer the standard library and the framework over a new dependency; pin what you add.

## Tests

- *Fast tests* cover every spec scenario plus the edge cases around it. *End-to-end tests* cover the main user journeys in a real browser.
- Before every commit: ruff check ., ruff format --check ., the fast suite. Changes touching templates, CSS or views also run the browser suite.
- Playwright: user-facing locators (get_by_role, get_by_label, the real UI texts), expect(...) auto-waiting, never fixed sleeps. Keep artifacts (trace, video, screenshots) in a git-ignored directory; --headed --slowmo to watch a run, playwright show-trace to replay one.
- A test must fail when the user-visible behaviour breaks: assert what the person sees (visible messages, values under their column headers), not only rows in the database.
- For important tests, break the behaviour on purpose in a throwaway copy of the repository and confirm the test fails.

## Verification before calling something done

1. Lint, format check, fast tests, and the browser suite when the UI changed.
2. An *independent review* against the specs by a fresh reviewer that did not write the code: it maps every scenario to a test, hunts for real defects with concrete failing scenarios, and ends with PASS or FAIL.
3. Run the real application and look at the result - screenshots for UI work.
4. Fix what the review found and review again until it passes.

## Git

- Conventional Commits in English, small and self-contained, one per task group, pushed only after verification passes.
- Never rewrite history or force-push without explicit consent, and back up the branch first.
- Keep generated files, databases and artifacts out of the repository.

## Data safety

- Treat the user's local database and files as production data until they say otherwise. Probe against throwaway copies (a path from an environment variable), never the real one.
- Back up before anything destructive and say where the backup is.
- Confirm before actions that are hard to undo or that reach the outside world.

## Documentation

- README.md must work on a clean clone; verify every command you put there.
- docs/: architecture (data model and flows, Mermaid diagrams), domain knowledge and open questions, operations, testing, and docs/worklog.md.
- docs/worklog.md gets one entry per task group: goal, what was built, deviations, verification, commit hashes - plus review results and manual checks.

## Delegating to subagents

- Give a self-contained prompt: files to read first, exact scope, decisions already made, rules above, and how to verify. State what the agent must *not* touch when several work in parallel.
- Subagents never commit, never change branches and never delete the user's data; the main session verifies their work and commits it.
- Use a separate agent for reviews, and give it permission to say FAIL.