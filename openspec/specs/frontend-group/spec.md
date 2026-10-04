# frontend-group Specification

## Purpose
Lets the mother and her close ones form a group around her, invite people with a link, and lets
the mother stay in charge of who is in it and whether it stays open.

## Requirements

### Requirement: Start a group
Right after sign-up, and whenever a signed-in person has no group, the frontend SHALL show a panel asking what they want to do: start a group as the mother, start a group as a partner, or wait for a link from a mother. Sign-up itself SHALL ask for no role. A person who already has groups SHALL be able to open the same panel from the group switcher. The mother choice SHALL be offered only to a person who is not yet the mother of a group. The role SHALL be called "Partner" and never "partnerka".

#### Scenario: Panel after sign-up
- **WHEN** a person finishes signing up
- **THEN** the panel with the three choices is shown

#### Scenario: Mother starts a group
- **WHEN** a person chooses to start a group as the mother
- **THEN** her start screen is shown with a step to invite her partner and close people at once

#### Scenario: Partner starts a group
- **WHEN** a person chooses to start a group as a partner
- **THEN** the waiting screen is shown with a step to invite the mother

#### Scenario: Waiting for a link
- **WHEN** a person chooses to wait for a link
- **THEN** they are told to ask a mother for a link and that no group is created

#### Scenario: Already a mother
- **WHEN** a person who is the mother of a group opens the panel
- **THEN** the mother choice is not offered

#### Scenario: Role wording
- **WHEN** any screen names the partner role
- **THEN** the word is "Partner" and "partnerka" appears nowhere

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
Opening `#/invite/<token>` SHALL show who invites, for which role, and until when, and SHALL let a signed-in person accept it, also when they already belong to other groups.

#### Scenario: Valid invitation
- **WHEN** a signed-in person opens a valid invitation link
- **THEN** the inviter's name and the offered role are shown with an accept button

#### Scenario: Accepting
- **WHEN** the person accepts the invitation
- **THEN** that group is selected and its start screen for the new role is shown

#### Scenario: Accepting with other groups
- **WHEN** a person who is the mother of one group accepts a `partner` or `supporter` invitation
- **THEN** both groups are available in the switcher and the new one is shown

#### Scenario: Unknown or expired invitation
- **WHEN** the invitation answers 404 `invitation_not_found`
- **THEN** a calm message says the link no longer works and suggests asking for a new one

#### Scenario: Already in a group
- **WHEN** accepting answers 409 `already_in_group`
- **THEN** the message from the error is shown and the person stays on the invitation screen

#### Scenario: Signed out
- **WHEN** a signed-out person opens an invitation
- **THEN** sign-in and sign-up are offered and the invitation is opened again afterwards

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

### Requirement: Group switcher
A person with more than one group SHALL see a switcher in the frame that names each group by its mother and the person's role in it ("Twoja grupa" for the group where they are the mother). Choosing a group SHALL change every group-bound screen to that group and its role, and SHALL be remembered in that browser.

#### Scenario: Two groups
- **WHEN** a person is the mother of one group and a supporter of another
- **THEN** the switcher lists both with the right role words

#### Scenario: Switching changes the screens
- **WHEN** the person switches from their own group to the other
- **THEN** the navigation and the start screen are those of a close person, and the next group-bound call carries the other group's id

#### Scenario: One group
- **WHEN** a person belongs to exactly one group
- **THEN** no switcher is shown, only the group's name in the frame

### Requirement: Invite at once
After starting a group, the mother SHALL be able to invite her partner and close people from her start screen, and a partner SHALL be able to invite the mother from the waiting screen. The frontend SHALL show the link `#/invite/<token>` with a copy button and its expiry date, and SHALL accept an optional e-mail.

#### Scenario: Mother invites a supporter
- **WHEN** the mother creates an invitation for a supporter
- **THEN** the full invitation link, a copy button and the expiry date are shown

#### Scenario: Mother invites her partner
- **WHEN** the mother creates an invitation for a partner
- **THEN** the link is shown and the role is named "Partner"

#### Scenario: Partner invites the mother
- **WHEN** the partner of a pending group creates an invitation for the mother
- **THEN** the link is shown

#### Scenario: Copy the link
- **WHEN** the person presses the copy button
- **THEN** a visible confirmation says the link was copied

#### Scenario: Closed group
- **WHEN** creating an invitation answers 409 `group_closed`
- **THEN** the message from the error is shown and no link is shown

### Requirement: Leave the group
A partner or a supporter SHALL be able to leave the selected group after a confirmation. The mother SHALL NOT be offered to leave an active group. After leaving, another group of the person is selected, or the panel is shown when none remains.

#### Scenario: Supporter leaves
- **WHEN** a supporter confirms leaving a group and has another group
- **THEN** the other group is shown

#### Scenario: Last group
- **WHEN** a supporter confirms leaving their only group
- **THEN** the panel for a person without a group is shown

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
