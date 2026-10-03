## MODIFIED Requirements

### Requirement: Start a group
A signed-in person without a group SHALL see three ways to begin: start a group as the mother, start one as a partner, or join as a close person. The close-person choice SHALL create nothing and SHALL explain that a link from the mother is needed. The role SHALL be called "Partner" and never "partnerka". The partner choice SHALL warn that the mother must not start her own group first.

#### Scenario: Mother starts a group
- **WHEN** a person without a group starts one as the mother
- **THEN** her start screen is shown and she is offered to invite her partner

#### Scenario: Partner starts a group
- **WHEN** a person without a group starts one as a partner
- **THEN** the waiting screen is shown with a step to invite the mother

#### Scenario: Close person
- **WHEN** a person without a group reads the close-person choice
- **THEN** it says they join with a link from the mother, and no group is created

#### Scenario: Role wording
- **WHEN** any screen names the partner role
- **THEN** the word is "Partner" and "partnerka" appears nowhere

### Requirement: Open an invitation
Opening `#/invite/<token>` SHALL show who invites, for which role, and until when, and SHALL let a signed-in person accept it. A signed-in person who is alone in their own group SHALL be offered to leave it and join, after a confirmation that names what is lost.

#### Scenario: Valid invitation
- **WHEN** a signed-in person without a group opens a valid invitation link
- **THEN** the inviter's name and the offered role are shown with an accept button

#### Scenario: Accepting
- **WHEN** the person accepts the invitation
- **THEN** their start screen for the new role is shown

#### Scenario: Unknown or expired invitation
- **WHEN** the invitation answers 404 `invitation_not_found`
- **THEN** a calm message says the link no longer works and suggests asking for a new one

#### Scenario: Alone in a pending group
- **WHEN** a partner alone in a pending group opens a `partner` or `supporter` invitation and confirms
- **THEN** the group is left, the invitation is accepted and the start screen of the new role is shown

#### Scenario: Mother alone in an active group
- **WHEN** a mother alone in her active group opens a `woman` invitation and confirms
- **THEN** her group is closed and left, the invitation is accepted and the new start screen is shown

#### Scenario: Already in a group
- **WHEN** accepting answers 409 `already_in_group`, or the person's group has other members
- **THEN** no leave-and-join choice is offered, the message from the error is shown and the person stays on the invitation screen

#### Scenario: Cancel the switch
- **WHEN** the person cancels the confirmation
- **THEN** nothing is changed

## ADDED Requirements

### Requirement: Leave the group
A partner or a supporter SHALL be able to leave their group after a confirmation. The mother SHALL NOT be offered to leave an active group.

#### Scenario: Supporter leaves
- **WHEN** a supporter confirms leaving
- **THEN** the screen for a person without a group is shown

#### Scenario: Mother has no leave control
- **WHEN** the mother opens the group screen of an active group
- **THEN** no leave control is shown

### Requirement: Issued invitations
The mother, and a partner of a pending group, SHALL see the unused invitations of the group with their role and expiry, and SHALL be able to revoke one.

#### Scenario: List
- **WHEN** the mother opens the group screen after creating an invitation
- **THEN** that invitation is listed with its role and expiry date

#### Scenario: Revoke
- **WHEN** the mother revokes a listed invitation
- **THEN** it disappears from the list

#### Scenario: Supporter
- **WHEN** a supporter opens the group screen
- **THEN** no invitation list is shown
