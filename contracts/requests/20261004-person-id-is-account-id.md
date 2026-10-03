# Request: say which id `Person.id` is

## What

In `components/schemas/Person` (used by `Task.created_by` and `Task.claimed_by`), document that
`id` is the account id, the same number as `Me.id`, and not a membership id.

Proposed change:

```yaml
Person:
  properties:
    id:
      type: integer
      description: Account id, the same value as `Me.id`. Not the membership id of `Member.id`.
```

## Why

The tasks screen shows the "Oznacz jako zrobione" button only on the task the signed-in person
took, and writes "Ty" for their own tasks. It finds them by comparing `claimed_by.id` and
`created_by.id` with `Me.id`. `Member.id` right next to it is explicitly a membership id, and in
every example the two numbers happen to be equal, so the contract does not settle it today.

If the backend fills `Person.id` with membership ids, the person who took a task never sees the
button to finish it.

## Optional, related

`Member` has no way to tell which row is the signed-in person. The group screen guesses by role
and name (safe for the mother, ambiguous for two loved ones with the same name). A boolean
`is_me` on `Member`, or the membership id on `Me.membership`, would remove the guess.

## Until then

The frontend assumes `Person.id` equals `Me.id`. A browser test in live mode
(`tests_e2e/test_live_flows.py`) pins this assumption with member ids that differ from account ids.
