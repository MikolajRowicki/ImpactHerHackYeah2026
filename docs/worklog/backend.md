# Worklog: backend session

One entry per task group. Change: `full-backend`, branch `change/full-backend`.

## Group 1: Contract additions and the frozen baseline

- **Goal:** the whole API is written down before any code, and v0 can no longer change by accident.
- **Built:**
  - `tests/tools/baseline.py` writes `contracts/baseline/v0.json`: per v0 operation a SHA-256 of its
    canonical JSON with every `$ref` resolved, per reachable schema and per example file the same.
    The example hash is taken from the parsed JSON, so line endings do not matter.
  - `tests/test_contract_baseline.py` names what changed. It is mutation-checked in a throwaway copy:
    an old schema field, an old response status and an old example file each make it fail.
  - 19 new operations and their schemas appended to `contracts/openapi.yaml` (no existing line
    removed, checked with `git diff`), and 72 new example files.
  - `tests/test_contract_additions.py` (privacy, roles, the nineteen operations, the voivodeship list).
  - `contracts/README.md` and the two messages in `docs/from-be-to-fe/` are final.
- **Deviations:**
  - The contract holds 23 operations, not 25; the artifacts that said 25 and "24 missing" are
    wrong. The baseline lists 23.
  - `release_task` joins `x-requires-active-group`, so the old guard test that listed exactly five
    marked operations now lists six.
  - `tests/test_frontend_operations.py` no longer demands that the frontend table equals the
    contract: entries it has must be exact and all v0 operations must be there. Otherwise the
    frontend session would need an `operations.js` change in this commit.
  - `accept_invitation` also answers 409 `role_taken` (spec) although its frozen text lists only
    `already_in_group` and `group_closed`; the code is documented in `contracts/README.md` and in the
    message to the frontend.
  - `leave_group` has `x-roles: [partner, supporter]`, and the woman gets 409 `cannot_remove_owner`
    from the application, as the spec says.
- **Verification:** `ruff check .`, `ruff format --check .`, `pytest tests` (618 passed).
- **Commit:** see the git log, subject `feat(contract): add the 19 operations after v0 and freeze v0`.
