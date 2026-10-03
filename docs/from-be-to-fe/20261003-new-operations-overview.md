# New operations coming with the full backend

Status: planned. They land in the contract in the first commit group of the change `full-backend`
(branch `change/full-backend`). This file is updated to `ready` with the commit when they are in.

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
| `leave_group` | partner, supporter | leave the group |
| `list_invitations`, `revoke_invitation` | woman, partner | see and cancel unused invitations |
| `delete_account` | signed in | delete the account and what the person wrote |
| `ai_say_it_for_me` | woman | a suggested message from what she wants to say; may answer `crisis: true` with help and no message |
| `ai_conversation_guide` | partner, supporter | opening lines, things to avoid and questions for a topic |
| the six account security operations | anyone / signed in | see `20261003-account-security-screens.md` |

## Rules for AI answers

- Every AI answer has `source`: `mock`, `groq` or `rules`. Show a visible note when it is `mock`
  (the foundation already has the mock notice pattern). `sources` is a list of `{title, url}`; it is
  empty now and will hold cited sources in a later change, so render it when it is not empty.
- When `crisis` is true, show the help block first and no suggested message.

## Demo data

After `seed_demo` runs, the example people sign in with the passwords documented in the README
(Anna, Piotr, Marta). The README will say how to start the live mode against that data.
