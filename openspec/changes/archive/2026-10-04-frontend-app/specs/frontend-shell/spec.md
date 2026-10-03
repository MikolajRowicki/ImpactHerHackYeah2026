# Spec Delta

## Purpose

The frame every MaydayMama screen shares: navigation that fits the person's role, calm light and
dark themes, a permanent place for help, clear loading and error states, and accessible layout.

## ADDED Requirements

### Requirement: Navigation fits the role
The frontend SHALL show navigation that matches the role of the signed-in person: the mother sees her start, her check-in, tasks, group and help; a partner or supporter sees their start, questions, tasks, group and help. A person without an active group sees no data sections.

#### Scenario: Mother navigation
- **WHEN** the mother is signed in and her group is active
- **THEN** the navigation offers start, check-in, tasks, group and help, and no questions section

#### Scenario: Loved one navigation
- **WHEN** a partner or supporter is signed in and the group is active
- **THEN** the navigation offers start, questions, tasks, group and help, and no check-in section

#### Scenario: No group yet
- **WHEN** a signed-in person belongs to no group
- **THEN** the navigation offers no check-in, questions or tasks sections

#### Scenario: Current place is marked
- **WHEN** a person opens a section from the navigation
- **THEN** that navigation item is marked as the current page for assistive technology

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

### Requirement: Help place is always reachable
Every screen SHALL offer a way to the help place, which explains calmly that help contacts will appear there and SHALL NOT show phone numbers or medical advice.

#### Scenario: Help from any screen
- **WHEN** any screen is shown, signed in or not
- **THEN** a link to the help place is visible and opens it

#### Scenario: No invented contacts
- **WHEN** the help place is shown
- **THEN** it contains no phone number

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
