# reminders Specification

## Purpose
Reminds people, gently and without detail, to do the small things that keep the circle working. Reminders appear in the app and can be sent by e-mail once a day.

## Requirements

### Requirement: In-app reminders
The API SHALL list what is due for the caller today (a day in Europe/Warsaw). The woman is reminded of a check-in when she has none today. A partner or a supporter is reminded of an observation when they gave none today. A member who claimed a task and has not finished it is reminded of it.

#### Scenario: Woman without a check-in
- **WHEN** the woman has no check-in today
- **THEN** the list holds a reminder of kind `check_in_due`

#### Scenario: Done for today
- **WHEN** she records a check-in
- **THEN** that reminder disappears

#### Scenario: Loved one
- **WHEN** a supporter has given no observation today
- **THEN** the list holds `observation_due`

#### Scenario: Open claimed task
- **WHEN** a member holds a claimed, unfinished task
- **THEN** the list holds `task_in_progress`

#### Scenario: Pending or closed group
- **WHEN** the group is not active
- **THEN** the list is empty

### Requirement: Reminder settings
A person SHALL turn e-mail reminders on or off. They are on by default.

#### Scenario: Default
- **WHEN** a person has never changed the setting
- **THEN** e-mail reminders are on

#### Scenario: Turn off
- **WHEN** a person saves `email_reminders: false`
- **THEN** the next send skips them

### Requirement: E-mail reminders
A command SHALL send one e-mail per person per reminder kind per day to people whose reminders are on and whose group is active. Running it again the same day SHALL send nothing new. E-mails SHALL contain no health data, no trend and no names of other members.

#### Scenario: Sent once
- **WHEN** the command runs twice on the same day
- **THEN** the second run sends no e-mail

#### Scenario: Opt-out respected
- **WHEN** a person turned reminders off
- **THEN** they receive none

#### Scenario: Generic content
- **WHEN** an e-mail is built
- **THEN** its text is general, in Polish, and contains no check-in value, trend or other member's name

#### Scenario: Console in the demo
- **WHEN** no mail server is configured
- **THEN** the message is written to the console and the command succeeds

#### Scenario: Same mail service
- **WHEN** a reminder is sent
- **THEN** it goes through the shared mail service, so SMTP settings, failure handling and the daily limit of the mailbox apply
