## REMOVED Requirements

### Requirement: Navigation fits the role
**Reason**: Navigation now depends on the place (general or one group) as well as the role.
**Migration**: Replaced by "Navigation fits the place and the role".

### Requirement: Help place is always reachable
**Reason**: The help place is no longer a placeholder without contacts.
**Migration**: Replaced by "Help is always reachable" and by `frontend-help`.

## ADDED Requirements

### Requirement: Navigation fits the place and the role
The frontend SHALL show a general part of the navigation to every signed-in person (start, education, help) and, when a group is selected, a group part that fits the person's role in that group: the mother sees check-in, tasks and group; a partner or supporter sees questions, tasks and group. A person without a group, or whose selected group is pending, sees no data sections.

#### Scenario: Mother in her group
- **WHEN** the mother is signed in and her selected group is active
- **THEN** the navigation offers start, education, help, check-in, tasks and group, and no questions section

#### Scenario: Loved one in a group
- **WHEN** a partner or supporter is signed in and the selected group is active
- **THEN** the navigation offers start, education, help, questions, tasks and group, and no check-in section

#### Scenario: Mother who is also a supporter elsewhere
- **WHEN** a person is the mother of one group and switches to a group where they are a supporter
- **THEN** the navigation changes to the supporter's, and switching back restores the mother's

#### Scenario: No group yet
- **WHEN** a signed-in person belongs to no group
- **THEN** the navigation offers start, education and help only

#### Scenario: Current place is marked
- **WHEN** a person opens a section from the navigation
- **THEN** that navigation item is marked as the current page for assistive technology

### Requirement: Help is always reachable
Every screen SHALL offer a way to the help place, signed in or not. The help place SHALL NOT give medical advice. Its contacts come from the backend (see `frontend-help`).

#### Scenario: Help from any screen
- **WHEN** any screen is shown, signed in or not
- **THEN** a link to the help place is visible and opens it

#### Scenario: Signed out
- **WHEN** a signed-out person opens the help place
- **THEN** it shows the emergency number 112 and a calm note that more help is available after signing in
