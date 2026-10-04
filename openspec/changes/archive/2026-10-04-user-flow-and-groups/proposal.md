## Why

The first manual run of the merged app showed wrong or confusing screens: a sample text and an invented "the last days were different" with no data behind it, "partner or partnerka" wording, and a group flow that does not work. Each person has to pick a role and start a group at once, so a mother and a partner who both have accounts end up in two separate groups and cannot invite each other. The model also does not fit real life: one person can be the mother of her own group and, at the same time, the partner or close person of other mothers. A visitor sees only a sign-in form, with no explanation of what the app is.

## What Changes

**Account and groups (backend and frontend)**
- Sign-up asks for nothing but name, e-mail and password. Right after it, a panel asks what the person wants to do: start a group as a **mother** (and invite her partner and close people at once), or start a group as a **partner** (and invite the mother), or wait for a link.
- One account can belong to **many groups**: the mother of one group (at most one), and the partner or close person of any number of others. A mother can be someone else's close person. The database allows one membership per person and group, and one membership as the mother per person.
- A person with several groups switches between them in the frame. Every group-bound call names the group in an `X-Group-Id` header. Without the header the first group is used, so v0 clients keep working.
- New operation `list_memberships` gives the switcher its data. v0 operations, schemas and examples do not change.
- Accepting an invitation no longer fails because the person is already in another group. It still fails when they are already in *that* group, or when a `woman` invitation meets a person who is already a mother elsewhere.
- The "leave my empty group and join" workaround from the earlier plan is dropped; many groups make it unnecessary.

**What each person sees**
- **Everyone, in no group or in any group**, has the same general place: education (what postpartum depression is, how to notice it, how to support, where to get help) and the help place with real contacts.
- **Inside a group**, the person sees the tools of their role in *that* group (mother: check-in, her summary, self-care, tasks; partner and close person: questions, summary with care reminder, tasks). Roles never mix between groups.

**Landing page:** a signed-out visitor sees a designed landing page (what the app is, the three roles, how it works, privacy promise, calm motion that respects reduced-motion) with sign-up and sign-in actions.

**Fixes from the first run**
- A narrative with source `mock` is no longer shown, and no "sample text" label exists. The `uncertain` trend sentence is true for "mixed" and "not enough data".
- The role is called "Partner" everywhere.
- Operations adopted by the frontend: `leave_group`, `list_invitations`, `revoke_invitation`, `delete_account`, `get_help`, `get_summary_extended`, `list_task_suggestions`, `list_memberships`. Mock mode mirrors all of them.

**Non-goals:** `get_preferences`, `update_preferences`, `list_reminders`, `ai_say_it_for_me`, `ai_conversation_guide`. A per-group URL scheme (`/groups/{id}/...`). Changing any v0 contract shape.

## Capabilities

### New Capabilities
- `frontend-landing`: the page a signed-out visitor sees.
- `frontend-education`: general education available to everyone.
- `frontend-help`: the help place with crisis lines and a care path.

### Modified Capabilities
- `group-membership`: many groups per person, selected group, listing memberships.
- `api-contract`: the `X-Group-Id` convention and the new operation.
- `frontend-group`: panel after sign-up, switcher, invitations, leaving.
- `frontend-summary`: mock narrative hidden, neutral wording, reasons and help.
- `frontend-account`: delete the account.
- `frontend-shell`: navigation by place and role, help for everyone.
- `frontend-tasks`: ready-made task suggestions.

## Impact

- Backend: `models/groups.py` and a migration, `permissions.py` (group resolution), `services/{accounts,groups,invitations,cleanup}.py`, new `list_memberships` route, `contracts/openapi.yaml` and examples, tests in `tests/`.
- Frontend: everything under `src/frontend/` (new landing, education, switcher, panel), mock store, e2e tests.
- Existing backend tests that assert "second group refused" change on purpose.
- `docs/screeny/` is already removed.

## Assumptions to confirm at review

1. **Hidden group of the mother:** the group is created when she picks "mother" in the panel, because check-ins and invitations need one. Until someone joins, the UI calls it "Twoja przestrzeń" and offers "invite your partner or close people".
2. A person is the mother in at most one group. Partner and close-person memberships are unlimited, but a person has at most one *pending* group started as a partner.
3. Default group without the header: the earliest membership. The frontend always sends the header once it knows the groups.
4. The education texts are my drafts in plain Polish, general and non-diagnostic; a specialist should read them before release.
5. `list_memberships` shows, per group, the mother's display name, which any member of that group already sees in `list_members`.
6. The landing page lives at `#/` for signed-out visitors; signed-in people see their start there as now.
7. Deleting an account as a mother deletes her group; the confirmation says so. As a partner or close person, only that person's memberships go.
8. The `uncertain` sentence: "Na razie nie da się powiedzieć nic pewnego. Przyglądamy się temu z uwagą i spokojem."
9. The help place calls `get_help` without a voivodeship (preferences are not adopted).
