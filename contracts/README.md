# API contract

`openapi.yaml` is the contract between the backend and the frontend. It is written by hand and is
the source of truth: the code follows it, not the other way round. It holds shapes, roles and
rules, no business logic.

## Reading it

- Every operation has an `operationId` (for example `get_me`), a list of allowed roles in
  `x-roles`, and the responses it can give.
- Roles: `woman`, `partner`, `supporter` (per group membership), `signed_in` (a session, no group
  needed), `anyone` (no session).
- `x-requires-active-group` marks operations that answer 409 `group_pending` until the woman has
  accepted her invitation, and 409 `group_closed` after she closed the group.
- Every error has the shape `{"error": {"code", "message", "fields"?}}`. Messages are Polish.
- Conventions (timestamps, CSRF, lists) are at the top of `openapi.yaml`.

## Examples

`examples/` holds one JSON file per request body and per declared response. The frontend mock
mode serves them, and the tests check them against the schemas.

| File name | Content |
|---|---|
| `<operationId>.<status>.json` | the response with that status, for example `get_me.200.json`, `get_me.401.json` |
| `<operationId>.request.json` | a valid request body, for example `login.request.json` |
| `<operationId>.<status>.<variant>.json` | another valid response for the same status, for example `get_me.200.partner.json` (the same person as a partner) |

The variants that exist today: `get_me.200.{partner,supporter,no_group,pending}`,
`get_summary.200.{partner,supporter}`, `create_group.201.partner`, and
`<operationId>.409.closed` for `create_task`, `claim_task`, `complete_task` and `accept_invitation`
(the group is closed, code `group_closed`).

Variants added after v0: `get_summary_extended.200.{partner,stable}`, `get_help.200.general`
(no voivodeship), `list_reminders.200.empty`, `ai_say_it_for_me.200.crisis` (the answer for a text
that matched the crisis rules: `crisis` is true, no message, with help) and
`release_task.409.closed`.

Example people: Anna (the woman, id 1), Piotr (partner, id 2), Marta (supporter, id 3).

## Versions: v0 is frozen

The 23 operations of v0 never change: not their paths, schemas, error codes or examples.
`contracts/baseline/v0.json` holds a fingerprint of each, and `tests/test_contract_baseline.py`
fails with the name of anything that changed or went missing. New behaviour is a new operation, a
new schema or a new example file; those are added to `openapi.yaml` and never rewrite what is above
them. A new method on an old path (for example `DELETE /api/v1/me`) is a new operation too. When a v0
response is not enough, a new operation carries more and the frontend moves to it.

The 19 operations added after v0 are:

| Area | Operations |
|---|---|
| Account | `delete_account`, `get_preferences`, `update_preferences` |
| Account security | `signup`, `activate_account`, `resend_activation`, `request_password_reset`, `confirm_password_reset`, `change_password` |
| Group | `leave_group`, `list_invitations`, `revoke_invitation` |
| Summary and help | `get_summary_extended`, `get_help` |
| Tasks and reminders | `list_task_suggestions`, `release_task`, `list_reminders` |
| AI | `ai_say_it_for_me`, `ai_conversation_guide` |

Two things follow from the freeze. The v0 text of `accept_invitation` lists only
`already_in_group` and `group_closed` for its 409; the backend also answers 409 `role_taken` when
the group already has a woman and a `woman` invitation is accepted. Handle an unknown 409 code by
showing its `message`. Links in e-mails have the forms `<APP_BASE_URL>#/activate/<token>` and
`<APP_BASE_URL>#/reset/<token>`.

## Asking for a change

Only the main session edits `openapi.yaml` and `examples/`. If you need a different shape:

1. Add a file `contracts/requests/<yyyymmdd>-<short-slug>.md`, for example
   `contracts/requests/20261003-task-due-date.md`. Say what you need, why, and the shape you
   propose. Keep going with your own mock data and mark it as such in the request.
2. Push your branch. The main session applies the request on `main`, deletes the request file in
   the same commit and tells you to merge `main`.

File names are unique, so two branches never edit the same file. Do not edit existing files in
`contracts/`.

## Checks

`pytest tests` validates the document, every example against its schema, the privacy and role
rules, and that the backend has no route the contract does not declare.
