## ADDED Requirements

### Requirement: Delete the account
A signed-in person SHALL be able to delete their account from the account screen, after a confirmation that says what is deleted. For the mother the confirmation SHALL say that the whole group and its data go too.

#### Scenario: Delete
- **WHEN** a person confirms deleting their account
- **THEN** they are signed out and the sign-in screen is shown

#### Scenario: Mother's warning
- **WHEN** the mother opens the delete confirmation
- **THEN** it says the group and its data are deleted

#### Scenario: Cancel
- **WHEN** the person cancels the confirmation
- **THEN** the account stays
