## MODIFIED Requirements

### Requirement: Many groups, one as the woman
A person SHALL be able to belong to many groups, at most once to each, and SHALL be the woman in at most one group. The application and the database SHALL enforce both rules. Both refusals use the code `already_in_group`, and their messages SHALL tell the two cases apart: already a member of that group, and already the woman of another group.

#### Scenario: Second group as a partner
- **WHEN** a person who is the woman of one group creates a group as a partner, or accepts a `partner` or `supporter` invitation
- **THEN** they belong to both groups

#### Scenario: Second group as the woman refused
- **WHEN** a person who is already the woman of a group creates another group as the woman
- **THEN** the response is 409 with code `already_in_group` and a message that says the person is already the woman of a group

#### Scenario: Woman invitation refused while the own group has content
- **WHEN** a person who is the woman of a group that is not empty accepts a `woman` invitation of another group
- **THEN** the response is 409 with code `already_in_group`, a message that says the person is already the woman of another group and that it must be closed and deleted first, and the invitation stays unused

#### Scenario: Same group twice refused
- **WHEN** a member accepts an invitation to the group they already belong to
- **THEN** the response is 409 with code `already_in_group` and a message that says the person already belongs to that group

#### Scenario: Concurrent creation
- **WHEN** the same person sends two create-group requests as the woman at once
- **THEN** exactly one group exists afterwards

### Requirement: Accepting an invitation
Accepting SHALL add the person to the group with the invited role and mark the invitation used, in one step that holds when two people accept at once. When the woman accepts the invitation of a pending group, the group becomes active. A person who is the woman of an empty group and accepts a `woman` invitation SHALL have that empty group replaced, as described in "Replacing an empty group".

#### Scenario: Woman accepts
- **WHEN** a person who is not the woman of any group accepts a `woman` invitation of a pending group
- **THEN** the response is 200 with their membership, and the group is active

#### Scenario: Member of other groups accepts
- **WHEN** a person who belongs to other groups accepts a `partner` or `supporter` invitation
- **THEN** the response is 200 and they belong to the new group as well

#### Scenario: Token used once
- **WHEN** two people accept the same token at once
- **THEN** one gets 200 and the other gets 404 with code `invitation_not_found`

#### Scenario: Group closed meanwhile
- **WHEN** the group was closed after the invitation was issued
- **THEN** the response is 409 with code `group_closed` and the invitation stays unused

#### Scenario: One woman per group
- **WHEN** a group already has a woman and a `woman` invitation exists for it
- **THEN** accepting it is refused with 409 and code `role_taken`, and nothing of the accepting person's own groups is deleted

## ADDED Requirements

### Requirement: Replacing an empty group
A group SHALL count as empty when its only member is the woman and it holds no check-in, no task and no observation, whether it is active or closed. When a person who is the woman of an empty group accepts a `woman` invitation, the empty group SHALL be deleted with its invitations, and the person SHALL join the invited group as the woman, in one transaction. If any part fails, the empty group, the person's membership and the invitation SHALL stay as they were.

#### Scenario: Empty active group is replaced
- **WHEN** a person who is the only member of her own active group, with no check-in, task or observation, accepts a `woman` invitation of a pending group
- **THEN** the response is 200, she is the woman of the invited group and it is active, her old group no longer exists, and the invitation is used

#### Scenario: Empty closed group is replaced
- **WHEN** a person who is the only member of her own closed group, with no data, accepts a `woman` invitation
- **THEN** the response is 200 and her old group no longer exists

#### Scenario: Issued invitations go with the group
- **WHEN** an empty group is replaced and it had an unused invitation
- **THEN** that token answers 404 with code `invitation_not_found` afterwards

#### Scenario: Other members keep the group
- **WHEN** the woman's own group has a second member and she accepts a `woman` invitation
- **THEN** the response is 409 with code `already_in_group` and her group is unchanged

#### Scenario: Any content keeps the group
- **WHEN** the woman's own group holds a check-in, a task or an observation and she accepts a `woman` invitation
- **THEN** the response is 409 with code `already_in_group`, her group is unchanged and the invitation stays unused

#### Scenario: Content added while accepting
- **WHEN** a task is added to her own group at the moment she accepts a `woman` invitation
- **THEN** either the task is saved and the accept is refused with 409, or the accept replaces the group and the task is refused; her group is never deleted together with a saved task

#### Scenario: Failure rolls everything back
- **WHEN** joining the invited group fails after the empty group was deleted
- **THEN** the empty group still exists, she is still its woman, and the invitation is unused
