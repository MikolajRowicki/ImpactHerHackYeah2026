# frontend-shell Specification

## Purpose
The frame every MaydayMama screen shares: navigation that fits the person's role, calm light and
dark themes, a permanent place for help, clear loading and error states, and accessible layout.

## Requirements

### Requirement: Screen the person may not use
The frontend SHALL show a calm explanation, not an error, when a person opens a section their role or group state does not allow.

#### Scenario: Loved one opens the check-in
- **WHEN** a partner opens the check-in address directly
- **THEN** the screen says this place belongs to the mother and links back to start

### Requirement: Light and dark theme
The frontend SHALL follow the system colour scheme by default and SHALL offer a visible switch between light and dark that is remembered in that browser.

#### Scenario: System dark
- **WHEN** the system prefers a dark colour scheme and the person never used the switch
- **THEN** the dark theme is shown

#### Scenario: Manual choice is remembered
- **WHEN** the person switches to the light theme and reloads the page
- **THEN** the light theme is shown regardless of the system setting

### Requirement: Readable contrast
Text and controls SHALL keep a contrast ratio of at least 4.5:1 for body text and 3:1 for large text and control borders in both themes.

#### Scenario: Body text in both themes
- **WHEN** a screen is shown in the light theme and in the dark theme
- **THEN** body text against its background has a contrast ratio of at least 4.5:1

### Requirement: Loading and failure states
While data loads the frontend SHALL show a loading state, and when a call fails it SHALL show the Polish message from the error, or a general message, with a way to try again.

#### Scenario: Failed call
- **WHEN** a screen's data call fails with an error body
- **THEN** the error's message is shown and a "try again" button reloads the screen

#### Scenario: Group not active
- **WHEN** an action answers 409 `group_pending` or `group_closed`
- **THEN** the message from the error is shown next to the action and the rest of the screen stays usable

### Requirement: Accessible structure
Every screen SHALL have exactly one level-one heading, landmarks for header, navigation and main content, a visible focus outline, and a label on every form field. Focus SHALL move to the new screen's heading after navigation.

#### Scenario: Field labels
- **WHEN** any form is shown
- **THEN** every field and every choice group can be found by its label

#### Scenario: Focus after navigation
- **WHEN** the person moves to another screen
- **THEN** keyboard focus is on that screen's main heading

### Requirement: Phone and laptop layout
Every screen SHALL be usable without horizontal scrolling at 375 pixels and SHALL use the extra width at 1280 pixels without stretching text lines beyond a comfortable reading width.

#### Scenario: Every screen at phone width
- **WHEN** each screen is shown in a 375 pixel wide window
- **THEN** none of them has a horizontal scrollbar

### Requirement: Unknown address
The frontend SHALL show a "page not found" screen with a way back to start for an unknown address.

#### Scenario: Unknown hash
- **WHEN** the person opens an address the app does not know
- **THEN** the not-found heading and a link back to start are shown

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
