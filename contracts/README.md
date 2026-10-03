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
  accepted her invitation.
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
`get_summary.200.{partner,supporter}`, `create_group.201.partner` and `create_task.409.closed`
(the group is closed, code `group_closed`).

Example people: Anna (the woman, id 1), Piotr (partner, id 2), Marta (supporter, id 3).

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
