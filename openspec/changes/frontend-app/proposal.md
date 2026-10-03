# Proposal

## Why

The repository has an API contract and a frontend shell with one placeholder screen. Design and
usability are 40% of the HackYeah score and the deadline is 2026-10-04 11:00, so the whole
product UI has to land now, in one change, against the contract and mock mode, while the backend
is built in parallel on another branch.

## What Changes

- A calm visual system: sage green base, cream background, one warm peach accent, a self-hosted
  rounded font, light and dark themes (follows the system, plus a manual switch that is
  remembered).
- An app frame: header, role-aware navigation (bottom bar on a phone, top bar on a laptop),
  loading, empty and error states, and a permanent calm "Pomoc" place for the later help path.
- Account screens: sign in, register, sign out; signed-out people are sent to sign in.
- Group screens: start a group as the mother or as a partner, the waiting state of a pending
  group, invite people with a shareable link, open and accept an invitation (`#/invite/<token>`),
  see members, and for the mother remove a member and close the group.
- The mother's space: a check-in with closed choices, her own history in words, her gentle
  summary, self-care suggestions.
- The loved ones' space: their summary with the care reminder, the closed observation
  questions, a thank-you after sending.
- Shared care tasks: list grouped by state, add, take, mark done.
- Mock mode becomes stateful: changes made in the demo (a check-in, a taken task, a new group)
  show up on screen, and a demo switch shows the app as the mother, a partner, a supporter,
  someone without a group or someone in a pending group.
- Browser tests for every main journey, docs and a frontend worklog.

## Capabilities

### New Capabilities

- `frontend-shell`: app frame, navigation per role, themes, help place, loading and error
  states, accessibility and layout rules shared by every screen.
- `frontend-account`: sign in, register, sign out and the signed-out redirect.
- `frontend-group`: starting a group, the pending state, invitations, members, removing a
  member and closing the group.
- `frontend-wellbeing`: the mother's check-in, her check-in history and self-care suggestions.
- `frontend-summary`: how the summary is shown to each role, the trend in gentle words and the
  care reminder.
- `frontend-observations`: the loved ones' closed questions about her daily life.
- `frontend-tasks`: shared care tasks.

### Modified Capabilities

- `frontend-mock-mode`: mock answers start from the contract examples but keep the changes made
  during the demo, and a demo switch picks the perspective.

## Non-goals

- Crisis contacts, phone numbers or medical advice. The help place stays a calm placeholder
  until the contract gets its fields.
- A separate coordination space for loved ones. The contract has no operation for it.
- Any change to `contracts/`, `src/backend/`, `tests/`, `pyproject.toml` or shared docs.
- PWA, offline mode, a framework or a build step. Translations other than Polish.

## Assumptions to confirm at review

1. Loved ones coordinate through the shared task list only; the "separate coordination space"
   from the brief needs a contract operation first.
2. The help place shows no phone numbers at all, not even 112, until the help path change.
3. Route paths are English (`#/check-in`, `#/tasks`); only `#/invite/<token>` is fixed by the
   contract.
4. Demo state lives in the browser tab (sessionStorage) and is cleared by `?mock=0` or by the
   "Zacznij demo od nowa" button.
5. The check-in history lists her entries in words and draws no chart, so nothing reads as a
   score.
6. A person may answer only some of the observation questions; at least one answer is needed.
7. The font is Nunito (SIL Open Font License), downloaded once and committed as `woff2` with the
   licence file.

## Impact

- `src/frontend/` is rebuilt: new CSS, screens, components, a mock store and strings.
- `tests_e2e/` gets journey tests; the shell tests change where the placeholder screen goes.
- New `docs/worklog/frontend.md`. Contract requests go to `contracts/requests/` if needed.
- No backend, contract or dependency changes. Backend work on its own branch is not touched.
