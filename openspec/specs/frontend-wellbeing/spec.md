# frontend-wellbeing Specification

## Purpose
Gives the mother a private, gentle place to note how she feels, look back at her own entries in
words, and find small self-care suggestions.

## Requirements

### Requirement: Check-in
The mother SHALL be able to record a check-in with three closed choices: mood, sleep and anxiety, each offered as labelled options in words with no numbers or scores.

#### Scenario: Saving a check-in
- **WHEN** the mother picks a mood, a sleep and an anxiety option and saves
- **THEN** a warm confirmation is shown and the new entry appears at the top of her history

#### Scenario: Missing choice
- **WHEN** the mother saves without picking one of the three
- **THEN** a message next to that choice asks her to pick one and nothing is sent

#### Scenario: Pending group
- **WHEN** saving answers 409 `group_pending`
- **THEN** the message from the error is shown and her choices stay selected

### Requirement: Check-in privacy note
The check-in screen SHALL tell the mother in plain words that only she sees her entries.

#### Scenario: Privacy note
- **WHEN** the check-in screen is shown
- **THEN** a note says that only she sees her entries

### Requirement: Her history
The mother SHALL see her own check-ins, newest first, each with its date and the three answers in words, and with no chart, number or score.

#### Scenario: History in words
- **WHEN** the mother opens her history
- **THEN** each entry shows its date and her mood, sleep and anxiety in words

#### Scenario: No entries yet
- **WHEN** she has no check-ins
- **THEN** a gentle empty state invites her to make the first one

### Requirement: Self-care suggestions
The mother SHALL see self-care suggestions with title, description and duration in minutes, each marked with an icon for its kind.

#### Scenario: Suggestions on her start
- **WHEN** the mother opens her start screen
- **THEN** the self-care suggestions are shown with their durations
