## MODIFIED Requirements

### Requirement: Open an invitation
Opening `#/invite/<token>` SHALL show who invites, for which role, and until when, and SHALL let a signed-in person accept it, also when they already belong to other groups. A signed-in person who is already the mother of a group and opens a `woman` invitation SHALL see, before accepting, what happens to their own group.

#### Scenario: Valid invitation
- **WHEN** a signed-in person opens a valid invitation link
- **THEN** the inviter's name and the offered role are shown with an accept button

#### Scenario: Accepting
- **WHEN** the person accepts the invitation
- **THEN** that group is selected and its start screen for the new role is shown

#### Scenario: Accepting with other groups
- **WHEN** a person who is the mother of one group accepts a `partner` or `supporter` invitation
- **THEN** both groups are available in the switcher and the new one is shown

#### Scenario: Mother opens a mother invitation
- **WHEN** a signed-in person who is the mother of a group opens a `woman` invitation
- **THEN** a notice says that an empty group of hers is replaced by the invited one and that a group with content must first be closed and deleted, and a link leads to her own group screen

#### Scenario: Mother's empty group is replaced
- **WHEN** that person accepts and her own group is empty
- **THEN** the invited group is selected and its start screen for the mother is shown, and the switcher no longer lists her old group

#### Scenario: Mother's group has content
- **WHEN** that person accepts and answers 409 `already_in_group`
- **THEN** the message from the error is shown, the person stays on the invitation screen, and the link to her own group screen stays visible

#### Scenario: Person who is not a mother
- **WHEN** a signed-in person who is not the mother of any group opens a `woman` invitation
- **THEN** no notice about replacing a group is shown

#### Scenario: Unknown or expired invitation
- **WHEN** the invitation answers 404 `invitation_not_found`
- **THEN** a calm message says the link no longer works and suggests asking for a new one

#### Scenario: Already in a group
- **WHEN** accepting answers 409 `already_in_group`
- **THEN** the message from the error is shown and the person stays on the invitation screen

#### Scenario: Signed out
- **WHEN** a signed-out person opens an invitation
- **THEN** sign-in and sign-up are offered and the invitation is opened again afterwards
