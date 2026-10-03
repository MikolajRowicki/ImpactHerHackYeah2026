# Spec Delta

## Purpose

Lets the woman record how she feels in a private daily check-in and gives her gentle self-care suggestions. Nobody else can read a check-in.

## ADDED Requirements

### Requirement: Recording a check-in
The woman of an active group SHALL record a check-in with mood, sleep and anxiety, each from its fixed set. A woman who records again on the same day SHALL add another check-in; nothing is overwritten.

#### Scenario: Valid check-in
- **WHEN** the woman posts mood `low`, sleep `little` and anxiety `some`
- **THEN** the response is 201 with the saved check-in and a UTC timestamp

#### Scenario: Value outside the set
- **WHEN** a value is not in its fixed set or a field is missing
- **THEN** the response is 422 with a Polish message per field

#### Scenario: Not the woman
- **WHEN** a partner or a supporter posts a check-in
- **THEN** the response is 403 with code `forbidden`

#### Scenario: Group not active
- **WHEN** the woman posts a check-in in a closed group
- **THEN** the response is 409 with code `group_closed`

### Requirement: Check-ins are private
Only the woman SHALL read check-ins, newest first, and only her own. No other operation returns a single check-in value to anyone else.

#### Scenario: Her list
- **WHEN** the woman lists check-ins
- **THEN** she receives her own check-ins, newest first

#### Scenario: Loved ones
- **WHEN** a partner or a supporter lists check-ins
- **THEN** the response is 403 with code `forbidden`

#### Scenario: Not leaked elsewhere
- **WHEN** a partner or a supporter calls summary, members, tasks and reminder operations after the woman recorded a check-in
- **THEN** no response contains a check-in value, a mood, a sleep value or an anxiety value as such

### Requirement: Self-care suggestions
The woman SHALL receive a fixed set of gentle suggestions covering breathing, relaxation, meditation and a walk, each with a title, a short description and a duration.

#### Scenario: List
- **WHEN** the woman calls `list_self_care`
- **THEN** the response holds at least one suggestion of each of the four kinds, in Polish

#### Scenario: Not for loved ones
- **WHEN** a partner calls `list_self_care`
- **THEN** the response is 403 with code `forbidden`
