# Spec Delta

## Purpose

Lets the mother and her close ones form a group around her, invite people with a link, and lets
the mother stay in charge of who is in it and whether it stays open.

## ADDED Requirements

### Requirement: Start a group
A signed-in person without a group SHALL be able to start one as the mother or as a partner, and SHALL be told how to join with an invitation link instead.

#### Scenario: Mother starts a group
- **WHEN** a person without a group starts one as the mother
- **THEN** her start screen is shown and she is offered to invite her partner

#### Scenario: Partner starts a group
- **WHEN** a person without a group starts one as a partner
- **THEN** the waiting screen is shown with a step to invite the mother

### Requirement: Waiting for the mother
While the group is pending, the frontend SHALL explain that the group starts when the mother accepts, SHALL let the partner create and copy her invitation link, and SHALL show no data sections.

#### Scenario: Pending group
- **WHEN** a partner of a pending group opens the app
- **THEN** the waiting explanation and the invitation step are shown, and no summary, tasks or questions

### Requirement: Invite people
The mother SHALL be able to invite a partner or a supporter; a partner SHALL be able to invite the mother while the group is pending. The frontend SHALL show the link `#/invite/<token>` with a copy button and its expiry date, and SHALL accept an optional e-mail.

#### Scenario: Mother invites a supporter
- **WHEN** the mother creates an invitation for a supporter
- **THEN** the full invitation link, a copy button and the expiry date are shown

#### Scenario: Copy the link
- **WHEN** the person presses the copy button
- **THEN** a visible confirmation says the link was copied

#### Scenario: Closed group
- **WHEN** creating an invitation answers 409 `group_closed`
- **THEN** the message from the error is shown and no link is shown

### Requirement: Open an invitation
Opening `#/invite/<token>` SHALL show who invites, for which role, and until when, and SHALL let a signed-in person accept it.

#### Scenario: Valid invitation
- **WHEN** a signed-in person without a group opens a valid invitation link
- **THEN** the inviter's name and the offered role are shown with an accept button

#### Scenario: Accepting
- **WHEN** the person accepts the invitation
- **THEN** their start screen for the new role is shown

#### Scenario: Unknown or expired invitation
- **WHEN** the invitation answers 404 `invitation_not_found`
- **THEN** a calm message says the link no longer works and suggests asking for a new one

#### Scenario: Already in a group
- **WHEN** accepting answers 409 `already_in_group`
- **THEN** the message from the error is shown and the person stays on the invitation screen

### Requirement: Members
Every member SHALL see the people in the group with their name and role in words. Only the mother SHALL see controls to remove a member, never for herself.

#### Scenario: Member list
- **WHEN** a member opens the group screen
- **THEN** every member's name and role in words are shown

#### Scenario: Mother removes a member
- **WHEN** the mother removes a supporter and confirms
- **THEN** that person disappears from the list

#### Scenario: Loved ones cannot remove
- **WHEN** a partner opens the group screen
- **THEN** no remove control is shown

### Requirement: Close the group
Only the mother SHALL be able to close the group, after a confirmation that says what closing means. A closed group SHALL be shown as closed to every member.

#### Scenario: Mother closes the group
- **WHEN** the mother confirms closing the group
- **THEN** the group screen says the group is closed and no invite or task actions are offered

#### Scenario: Cancel closing
- **WHEN** the mother opens the close confirmation and cancels
- **THEN** the group stays active
