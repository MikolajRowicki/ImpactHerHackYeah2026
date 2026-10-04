# group-membership Specification

## Purpose
Defines who belongs to a group, who owns it and how people join, leave or are removed. The woman owns the group and decides who is in it.

## Requirements

### Requirement: Many groups, one as the woman
A person SHALL be able to belong to many groups, at most once to each, and SHALL be the woman in at most one group. The application and the database SHALL enforce both rules.

#### Scenario: Second group as a partner
- **WHEN** a person who is the woman of one group creates a group as a partner, or accepts a `partner` or `supporter` invitation
- **THEN** they belong to both groups

#### Scenario: Second group refused
- **WHEN** a person who is already the woman of a group creates another group as the woman, or accepts a `woman` invitation
- **THEN** the response is 409 with code `already_in_group`

#### Scenario: Same group twice refused
- **WHEN** a member accepts an invitation to the group they already belong to
- **THEN** the response is 409 with code `already_in_group`

#### Scenario: Concurrent creation
- **WHEN** the same person sends two create-group requests as the woman at once
- **THEN** exactly one group exists afterwards

### Requirement: Group creation by role
The woman SHALL create an active group. A partner SHALL create a pending group, and SHALL have at most one pending group at a time. A supporter SHALL NOT create a group.

#### Scenario: Woman creates
- **WHEN** a person who is not the woman of any group creates a group with role `woman`
- **THEN** the group is active and the person is its woman

#### Scenario: Partner creates
- **WHEN** a person creates a group with role `partner`
- **THEN** the group is pending and holds only the partner

#### Scenario: Second pending group refused
- **WHEN** a person who is the partner of a pending group creates another group with role `partner`
- **THEN** the response is 409 with code `already_in_group`

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
- **THEN** accepting it is refused with 409 and code `role_taken`

### Requirement: Members list
Every member SHALL see the members of their group with display name, role and join time, and the membership id.

#### Scenario: List
- **WHEN** a member calls `list_members`
- **THEN** the response lists every member of their group and no one from another group

### Requirement: Removing members and closing the group
Only the woman SHALL remove a member or close the group. Removal deletes the member's observation answers in that group and returns tasks they claimed there to open. Closing a closed group SHALL return it unchanged. A removed person keeps their other groups.

#### Scenario: Woman removes a supporter
- **WHEN** the woman removes a supporter
- **THEN** the response is 200, the supporter is no longer in that group, their other groups remain, and their answers no longer count in the trend

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
A partner or a supporter SHALL be able to leave the selected group. The woman SHALL NOT leave an active group; she closes it instead. The woman SHALL be able to leave a closed group, which deletes the group with all its data, and she SHALL then be able to create a new group as the woman.

#### Scenario: Supporter leaves
- **WHEN** a supporter calls `leave_group`
- **THEN** the response is 200, they are no longer in that group, their other groups remain, their observation answers there are deleted and their claimed tasks there are open again

#### Scenario: Woman tries to leave an active group
- **WHEN** the woman calls `leave_group` while the group is active
- **THEN** the response is 409 with code `cannot_remove_owner` and she stays in the group

#### Scenario: Woman leaves a closed group
- **WHEN** the woman closes the group and then calls `leave_group`
- **THEN** the response is 200, the group and its data are deleted, every former member is out of it, and she can create a new group as the woman

### Requirement: Managing issued invitations
The woman, and the partner of a pending group, SHALL list the unused invitations of their group and revoke one.

#### Scenario: List and revoke
- **WHEN** the woman lists invitations and revokes one
- **THEN** the revoked token answers 404 on preview and no longer appears in the list

#### Scenario: Supporter
- **WHEN** a supporter lists or revokes invitations
- **THEN** the response is 403 with code `forbidden`

### Requirement: Group integrity in the database
The database SHALL refuse a second membership for one person in one group, a second membership as the woman for one person, a second woman in one group and a used invitation that is used again.

#### Scenario: Constraint holds without the application
- **WHEN** a row that breaks one of these rules is inserted directly
- **THEN** the database rejects it

### Requirement: Selected group
Every operation that works inside a group SHALL use the group named in the `X-Group-Id` request header. Without the header it SHALL use the person's earliest membership. A header naming a group the person does not belong to SHALL be refused.

#### Scenario: Header selects the group
- **WHEN** a person in two groups calls `list_members` with `X-Group-Id` of the second
- **THEN** the response lists the members of the second group, and their role there decides what they may do

#### Scenario: No header
- **WHEN** a person in two groups calls `list_members` without the header
- **THEN** the response lists the members of their earliest group

#### Scenario: Not a member
- **WHEN** the header names a group the person does not belong to
- **THEN** the response is 403 with code `not_a_member`

#### Scenario: Invalid header
- **WHEN** the header is not a whole number
- **THEN** the response is 422

#### Scenario: Me follows the header
- **WHEN** `get_me` is called with the header
- **THEN** its `membership` is the person's membership in that group

### Requirement: Listing memberships
The API SHALL list every group of the caller with the group id, the caller's role, the group status and the display name of the group's woman (null while none).

#### Scenario: Several groups
- **WHEN** a person who is the mother of one group and the supporter of another calls `list_memberships`
- **THEN** both are listed, each with the person's role in it

#### Scenario: No group
- **WHEN** a person without a group calls `list_memberships`
- **THEN** the response is 200 with an empty list

#### Scenario: Signed out
- **WHEN** no session exists
- **THEN** the response is 401
