# frontend-help Specification

## Purpose
TBD - created by archiving change user-flow-and-groups. Update Purpose after archive.

## Requirements

### Requirement: Crisis lines and care path
A signed-in person SHALL see the crisis lines (name, number, hours, description) and the care path steps in order, from `get_help`. A phone number SHALL be a link that dials it.

#### Scenario: Help shown
- **WHEN** a signed-in person opens the help place
- **THEN** every crisis line and every path step from the answer is shown in order

#### Scenario: Number is dialable
- **WHEN** a crisis line is shown
- **THEN** its number is a `tel:` link

### Requirement: Not a diagnosis
The help place SHALL say that the app does not diagnose and does not replace a doctor.

#### Scenario: Notice
- **WHEN** the help place is shown
- **THEN** a visible note says the app is not a doctor and gives no diagnosis

### Requirement: Failure is calm
When `get_help` fails, the help place SHALL still show 112 and a way to try again.

#### Scenario: Failed call
- **WHEN** `get_help` fails
- **THEN** the number 112 is shown with the error message and a retry button
