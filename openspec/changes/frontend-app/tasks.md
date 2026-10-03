# Tasks

Every group is one commit. Before each commit: `poetry run ruff check .`,
`poetry run ruff format --check .`, `poetry run pytest`, `poetry run pytest tests_e2e`, and an
entry in `docs/worklog/frontend.md` (goal, what was built, deviations, verification, hash).
Groups 2, 3 and 4 may run in parallel after group 1; each touches only the files it owns
(design.md, decision 6).

## 1. Foundation: visual system, frame, router, session, mock store

- [x] 1.1 Add Nunito variable `woff2` (latin, latin-ext) and `OFL.txt` under `src/frontend/fonts/`; verify the files load with status 200 from the static server
- [x] 1.2 Rewrite `css/tokens.css` with the light and dark palette, type scale, spacing, radii and shadows from design.md; add `css/components.css` (buttons, cards, chips, choice cards, fields, notices, nav, dialog) and empty `css/screens/<area>.css` files linked from `index.html`; verify the page renders in both themes
- [x] 1.3 Add the pre-paint theme script in `index.html` and a header switch that stores the choice; verify with an e2e test for "System dark" and "Manual choice is remembered"
- [x] 1.4 Add `js/icons.js`, `js/ui/layout.js`, `js/ui/forms.js`, `js/ui/feedback.js`, `js/ui/dialog.js`; verify through the screens that use them in 1.7 and 1.8
- [x] 1.5 Extend the router to path patterns with params, add `js/session.js`, the signed-out redirect with the remembered path, role and group guards, the calm "not for you" screen, and focus on the h1 after navigation; verify with e2e tests for "Focus after navigation", "Loved one opens the check-in" and "Unknown hash"
- [x] 1.6 Add `js/mock-store.js` with sessionStorage state, mutations and mirrored rule errors, the perspective switch and the reset button in the mock notice, and `?mock=0` clearing the state; verify with e2e tests for every `frontend-mock-mode` scenario
- [x] 1.7 Build the app frame: header with brand, theme switch and sign-out, role-aware navigation (top on wide, bottom on phone) with `aria-current`, loading and error-with-retry states, and the `#/help` place with no phone numbers; verify with e2e tests for the navigation scenarios, "Help from any screen", "No invented contacts" and "Failed call"
- [x] 1.8 Restructure `strings.pl.js` into area keys; replace the placeholder home with a start screen router stub per role; update `tests_e2e/test_mock_mode.py`, `test_live_mode.py` and `test_layout.py` to the new texts; verify the full e2e suite passes
- [x] 1.9 Build the summary card shared by all roles (statements, narrative with sample label, trend sentence and icon, help link on `needs_attention`, local time, care reminder slot) in `js/ui/summary.js`; verify with e2e tests on the start stubs for every `frontend-summary` scenario, using the partner perspective for the care reminder and needs-attention cases
- [x] 1.10 Create `docs/worklog/frontend.md` with the group 1 entry and commit `feat(frontend): visual system, app frame and stateful mock`

## 2. Account and group screens

- [x] 2.1 Build `#/login` and `#/register` with field labels, client checks (password length 8) and server field errors; verify with e2e tests for every `frontend-account` scenario
- [x] 2.2 Build onboarding (start as mother or partner, how to join by link) and the pending waiting screen with the mother's invitation step; verify with e2e tests for "Mother starts a group", "Partner starts a group" and "Pending group"
- [x] 2.3 Build invitation creation with role choice, optional e-mail, full link, copy button with confirmation and expiry date; verify with e2e tests for "Mother invites a supporter", "Copy the link" and "Closed group"
- [x] 2.4 Build `#/invite/:token` with preview, accept, signed-out path and error states; verify with e2e tests for every "Open an invitation" scenario
- [x] 2.5 Build `#/group` with members and roles in words, the mother's remove with dialog confirmation, and close group with confirmation and closed state; verify with e2e tests for the "Members" and "Close the group" scenarios
- [x] 2.6 Add the worklog entry and commit `feat(frontend): account, onboarding, invitations and group screens`

## 3. The mother's space

- [x] 3.1 Build the mother's start screen: greeting, summary, check-in call to action, self-care cards with kind icons and minutes, open tasks preview; verify with e2e tests for "Mother's summary" and "Suggestions on her start"
- [x] 3.2 Build `#/check-in` with three choice groups in words, privacy note, warm confirmation, and history in words newest first with an empty state; verify with e2e tests for every `frontend-wellbeing` scenario
- [x] 3.3 Add the worklog entry and commit `feat(frontend): check-in, history, self-care and summary`

## 4. The loved ones' space and shared tasks

- [x] 4.1 Build the loved ones' start screen: summary card from 1.9 with care reminder, call to action to the questions, open tasks preview; verify with the e2e test "Loved one's summary with care reminder"
- [x] 4.2 Build `#/questions` with radio choices, the privacy note, partial answers, the at-least-one check and the thank-you screen that never shows answers back; verify with e2e tests for every `frontend-observations` scenario
- [x] 4.3 Build `#/tasks` grouped as open, taken and done, add form with length limits, take and done controls by rule, conflict reload, no per-person counts; verify with e2e tests for every `frontend-tasks` scenario
- [x] 4.4 Add the worklog entry and commit `feat(frontend): observations and shared tasks`

## 5. Integration checks and hand-off

- [ ] 5.1 Add the contrast test (body text, secondary text, primary and accent buttons, both themes) and the 375 px layout sweep over every route; fix tokens or layout until both pass
- [ ] 5.2 Run an independent review by a fresh agent against all spec deltas: every scenario mapped to a test, concrete defects listed, PASS or FAIL; fix and repeat until PASS
- [ ] 5.3 Run the app (static mock and Django) and take screenshots of every main screen at 375 px and 1280 px in both themes into `test-results/`; check them by eye
- [ ] 5.4 Write the final worklog entry (review result, screenshots checked, screens checked only in mock mode, contract requests waiting) and commit `test(frontend): contrast and layout checks`; push `change/frontend-app`
