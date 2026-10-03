# Spec Delta

## ADDED Requirements

### Requirement: Demo changes stay visible
In mock mode, changes the person makes SHALL be reflected on screen for the rest of the browser tab session: a saved check-in, an added, taken or finished task, a started or closed group, a removed member, signing in and out. No request SHALL go to the backend.

#### Scenario: Task taken in the demo
- **WHEN** in mock mode a person takes an open task and reloads the page
- **THEN** the task is still shown as taken by them and no request went to `/api/v1`

#### Scenario: Reset the demo
- **WHEN** the person presses the demo reset button
- **THEN** the screens show the contract examples again

### Requirement: Demo perspective switch
In mock mode, the notice SHALL offer a switch between the perspectives mother, partner, supporter, no group and pending group, and SHALL show the app as that person.

#### Scenario: Switch to partner
- **WHEN** the person picks the partner perspective in the mock notice
- **THEN** the start screen of the partner Piotr with his summary is shown

#### Scenario: No switch in live mode
- **WHEN** mock mode is off
- **THEN** no perspective switch is shown
