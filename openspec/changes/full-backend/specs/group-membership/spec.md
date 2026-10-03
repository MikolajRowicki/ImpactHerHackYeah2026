# Spec Delta

## Purpose

Defines who belongs to a group, who owns it and how people join, leave or are removed. The woman owns the group and decides who is in it.

## ADDED Requirements

### Requirement: One group per person
A person SHALL belong to at most one group, enforced by the application and by the database.

#### Scenario: Second group refused
- **WHEN** a person who is in a group creates another one or accepts an invitation
- **THEN** the response is 409 with code `already_in_group`

#### Scenario: Concurrent creation
- **WHEN** the same person sends two create-group requests at once
- **THEN** exactly one group exists afterwards

### Requirement: Group creation by role
The woman SHALL create an active group. A partner SHALL create a pending group. A supporter SHALL NOT create a group.

#### Scenario: Woman creates
- **WHEN** a person without a group creates a group with role `woman`
- **THEN** the group is active and the person is its woman

#### Scenario: Partner creates
- **WHEN** a person without a group creates a group with role `partner`
- **THEN** the group is pending and holds only the partner

#### Scenario: Supporter creates
- **WHEN** a supporter tries to create a group
- **THEN** the response is 422 with a message under `fields.role`

### Requirement: Pending group stays empty
A pending group SHALL hold no data and SHALL accept no check-ins, observations or tasks until the woman accepts an invitation.

#### Scenario: Data refused while pending
- **WHEN** a member of a pending group creates a task or an observation
- **THEN** the response is 409 with code `group_pending`

### Requirement: Invitations
The API SHALL issue single-use invitations that expire after 7 days. The woman invites a partner or a supporter. A partner invites only the woman, and only while the group is pending. A supporter invites nobody.

#### Scenario: Woman invites a supporter
- **WHEN** the woman creates an invitation with role `supporter`
- **THEN** the response is 201 with a token and an expiry 7 days ahead

#### Scenario: Partner invites the woman
- **WHEN** the partner of a pending group creates an invitation with role `woman`
- **THEN** the response is 201

#### Scenario: Role not allowed
- **WHEN** a partner invites a supporter, a supporter invites anyone, or the woman invites a woman
- **THEN** the response is 403 with code `role_not_allowed`

#### Scenario: Optional e-mail
- **WHEN** an invitation request carries an e-mail
- **THEN** a message with the invitation link is sent to that address and the response is unchanged

#### Scenario: Closed group
- **WHEN** a member asks for an invitation in a closed group
- **THEN** the response is 409 with code `group_closed`

### Requirement: Invitation preview
The API SHALL show what an invitation offers without a session: the role, the display name of the inviter, the group status and the expiry. It SHALL reveal nothing else about the group.

#### Scenario: Valid token
- **WHEN** a client without a session reads a valid, unused, unexpired token
- **THEN** the response is 200 with exactly those four fields

#### Scenario: Unusable token
- **WHEN** the token is unknown, used, revoked or expired
- **THEN** the response is 404 with code `invitation_not_found`, with the same answer for each reason

### Requirement: Accepting an invitation
Accepting SHALL add the person to the group with the invited role and mark the invitation used, in one step that holds when two people accept at once. When the woman accepts the invitation of a pending group, the group becomes active.

#### Scenario: Woman accepts
- **WHEN** a person without a group accepts a `woman` invitation of a pending group
- **THEN** the response is 200 with their membership, and the group is active

#### Scenario: Token used once
- **WHEN** two people accept the same token at once
- **THEN** one gets 200 and the other gets 404 with code `invitation_not_found`

#### Scenario: Group closed meanwhile
- **WHEN** the group was closed after the invitation was issued
- **THEN** the response is 409 with code `group_closed` and the invitation stays unused

#### Scenario: One woman per group
- **WHEN** a group already has a woman and a `woman` invitation exists for it
- **THEN** accepting it is refused with 409 and code `role_taken`

### Requirement: Members list
Every member SHALL see the members of their group with display name, role and join time, and the membership id.

#### Scenario: List
- **WHEN** a member calls `list_members`
- **THEN** the response lists every member of their group and no one from another group

### Requirement: Removing members and closing the group
Only the woman SHALL remove a member or close the group. Removal deletes the member's observation answers and returns tasks they claimed to open. Closing a closed group SHALL return it unchanged.

#### Scenario: Woman removes a supporter
- **WHEN** the woman removes a supporter
- **THEN** the response is 200, the supporter has no group, and their answers no longer count in the trend

#### Scenario: Not the woman
- **WHEN** a partner or a supporter removes a member or closes the group
- **THEN** the response is 403 with code `forbidden`

#### Scenario: Remove herself
- **WHEN** the woman removes her own membership
- **THEN** the response is 409 with code `cannot_remove_owner`

#### Scenario: Member of another group
- **WHEN** the woman removes a membership id from another group
- **THEN** the response is 404 with code `not_found`

#### Scenario: Close
- **WHEN** the woman closes an active group
- **THEN** its status is `closed` and data operations answer 409 with code `group_closed`

### Requirement: Leaving a group
A partner or a supporter SHALL be able to leave their group. The woman SHALL NOT leave; she closes the group instead.

#### Scenario: Supporter leaves
- **WHEN** a supporter calls `leave_group`
- **THEN** the response is 200, they have no group, their observation answers are deleted and their claimed tasks are open again

#### Scenario: Woman tries to leave
- **WHEN** the woman calls `leave_group`
- **THEN** the response is 409 with code `cannot_remove_owner`

### Requirement: Managing issued invitations
The woman, and the partner of a pending group, SHALL list the unused invitations of their group and revoke one.

#### Scenario: List and revoke
- **WHEN** the woman lists invitations and revokes one
- **THEN** the revoked token answers 404 on preview and no longer appears in the list

#### Scenario: Supporter
- **WHEN** a supporter lists or revokes invitations
- **THEN** the response is 403 with code `forbidden`

### Requirement: Group integrity in the database
The database SHALL refuse a second membership for one person, a second woman in one group and a used invitation that is used again.

#### Scenario: Constraint holds without the application
- **WHEN** a row that breaks one of these rules is inserted directly
- **THEN** the database rejects it
