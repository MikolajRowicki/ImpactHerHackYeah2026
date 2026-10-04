## 1. Wording, summary and mock narrative

- [x] 1.1 Replace every "partner lub partnerka", "partnerka" and related forms in `strings.pl.js` with "Partner" forms.
- [x] 1.2 Hide a `mock` narrative in `ui/summary.js`; remove the `sample` string and chip style.
- [x] 1.3 Neutral `uncertain` sentences (mother and loved-one versions).
- [x] 1.4 Tests: hidden mock narrative, uncertain sentence, no "partnerka" on the main screens.
- [x] 1.5 Verify: `ruff check .`, `ruff format --check .`, `pytest tests`, `pytest tests_e2e`. Commit.

## 2. Backend: many groups per person

- [x] 2.1 Model and migration: `Membership.user` to a foreign key, constraints `(user, group)` and one woman per user; reversible with a guard; migration tested forward and backward.
- [x] 2.2 `member_context`: resolve the group from `X-Group-Id` (422 for a bad value, 403 `not_a_member` for a foreign group), default earliest membership. `accounts.me` uses the same resolution.
- [x] 2.3 Services: `create_group` (one mother, one pending partner group), `accept` (already in this group, second mother), `leave`, `remove_member`, `cleanup` and `delete_account` per group.
- [x] 2.4 `list_memberships` route, schema, examples and contract text (`X-Group-Id` convention); `contracts/README.md` operation table; update the operation count text if it is asserted.
- [x] 2.5 Tests for every new scenario of `group-membership` (two groups, different roles, header rules, constraints, concurrency); change the old "second group refused" tests on purpose; baseline guard passes.
- [x] 2.6 `seed_demo`: one person who is the mother of one group and a supporter in another.
- [x] 2.7 Verify as in 1.5. Commit.

## 3. Frontend: accounts, panel and group switcher

- [x] 3.1 `operations.js`: `list_memberships`, `leave_group`, `list_invitations`, `revoke_invitation`, `delete_account`; extend `tests/test_frontend_operations.py`.
- [x] 3.2 Session: memberships and selected group (remembered, validated); `api.js` sends `X-Group-Id` except for account-level calls.
- [x] 3.3 Mock store: memberships per person, selected group, the new operations.
- [x] 3.4 Panel after sign-up and "Dodaj grupę" dialog; mother hidden when already a mother; waiting-for-link choice.
- [x] 3.5 Switcher in the frame; navigation built from the general part and the group part by role.
- [x] 3.6 Invitations: invite at once from the mother's start; accept with other groups; issued list with revoke; leave group with confirmation.
- [x] 3.7 Tests (mock mode and live with routed answers): panel, both starts, switching changes nav and header, mother-and-supporter person, accept with other groups, leave, list and revoke, mother hidden.
- [x] 3.8 Verify, including the live e2e against the real backend. Commit.

## 4. Education, help, summary and tasks

- [ ] 4.1 `get_help`, `get_summary_extended`, `list_task_suggestions` in `operations.js` and the mock store.
- [ ] 4.2 Education screen and content; start without a group with education and help entries.
- [ ] 4.3 Help place from `get_help` (lines, `tel:` links, ordered path, notice, calm failure, signed-out view with 112).
- [ ] 4.4 Summary: use the extended answer; reasons and crisis lines for `needs_attention`.
- [ ] 4.5 Tasks screen: suggestions card.
- [ ] 4.6 Account screen: delete account with the mother's warning.
- [ ] 4.7 Tests for each scenario above. Verify as in 1.5. Commit.

## 5. Landing page

- [ ] 5.1 Landing screen at the root for visitors: hero, roles, how it works, privacy, not-a-doctor note, final call to action; `frontend-design` guidance for look and motion.
- [ ] 5.2 Motion with `IntersectionObserver` and CSS, disabled under reduced motion; inline SVG illustrations; light and dark theme.
- [ ] 5.3 Tests: root shows landing when signed out and start when signed in, invitation link bypasses it, roles blocks, reduced motion, no horizontal scroll at 375 px, contrast in both themes.
- [ ] 5.4 Verify. Commit.

## 6. Review and wrap-up

- [ ] 6.1 Update `docs/architecture.md` (data model with many memberships, header flow) and `docs/worklog/` (backend and frontend entries per group).
- [ ] 6.2 Independent review against all specs by a fresh reviewer; fix and repeat until PASS.
- [ ] 6.3 Run the real app, take screenshots of the panel, switcher, landing, education and help; check by eye.
- [ ] 6.4 Archive the change before merging.
