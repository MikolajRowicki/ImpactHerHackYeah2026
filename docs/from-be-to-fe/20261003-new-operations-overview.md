# New operations coming with the full backend

Status: ready. They are in `contracts/openapi.yaml` on the branch `change/full-backend`, commit
`d4f26df`, with examples in `contracts/examples/`. Merge that branch (or `main` after it is merged).
The backend that answers them arrives in later commits of the same branch; until then use mock mode.
`contracts/README.md` lists them by area.

## The rule

The 25 operations of the contract v0 never change: same paths, schemas, error codes and examples.
New behaviour is a new operation. When a v0 response is not enough (for example the summary), a
new operation carries more, and you may move to it. Everything in v0 keeps working.

## New operations

| Operation | Roles | What it gives the UI |
|---|---|---|
| `get_summary_extended` | all | the summary plus `reasons` (why the trend is what it is) and `help` (crisis lines and a care path, only when the trend needs attention) |
| `get_help` | signed in | crisis lines and the care path for a voivodeship (query `voivodeship`, or the saved one) |
| `get_preferences`, `update_preferences` | signed in | voivodeship and the e-mail reminder switch |
| `list_reminders` | all | what is due today: check-in, observation, a task in progress |
| `list_task_suggestions` | all | ready-made care tasks to add in one tap |
| `release_task` | all | the person who claimed a task hands it back |
| `leave_group` | all | partner and supporter leave; the woman only after closing the group, and then the whole group is deleted with its data (ask her to confirm first); 409 `cannot_remove_owner` while it is active |
| `list_invitations`, `revoke_invitation` | woman, partner | see and cancel unused invitations |
| `delete_account` | signed in | delete the account and what the person wrote |
| `ai_say_it_for_me` | woman | a suggested message from what she wants to say; may answer `crisis: true` with help and no message |
| `ai_conversation_guide` | partner, supporter | opening lines, things to avoid and questions for a topic |
| the six account security operations | anyone / signed in | see `20261003-account-security-screens.md` |

## Example variants to look at

`get_summary_extended.200` (woman, with help), `.200.partner` (with a care reminder and the general
help), `.200.stable` (no help); `get_help.200` and `.200.general`; `list_reminders.200` and
`.200.empty`; `ai_say_it_for_me.200` and `.200.crisis`; `release_task.409.closed`.

## One more code

`accept_invitation` can answer 409 with the code `role_taken` (the group already has a woman). The
v0 text cannot list it because v0 is frozen. Show the `message` of any unknown 409 code.

## Rules for AI answers

- Every AI answer has `source`: `mock`, `groq` or `rules`. Show a visible note when it is `mock`
  (the foundation already has the mock notice pattern). `sources` is a list of `{title, url}`; it is
  empty now and will hold cited sources in a later change, so render it when it is not empty.
- When `crisis` is true, show the help block first and no suggested message.

## Demo data

After `seed_demo` runs, the example people sign in with the passwords documented in the README
(Anna, Piotr, Marta). The README will say how to start the live mode against that data.
