# demo-data Specification

## Purpose
Fills a database with the example people and two weeks of believable data so the demo and live-mode tests start from a known state.

## Requirements

### Requirement: Seed command
A command SHALL create Anna (the woman), Piotr (partner) and Marta (supporter) with a known password, one active group, 14 days of check-ins, observations, tasks in every status and one unused invitation.

#### Scenario: Fresh database
- **WHEN** the command runs on an empty database
- **THEN** the three accounts can sign in, and Anna's summary shows a trend of `needs_attention`

#### Scenario: Matches the contract examples
- **WHEN** Anna calls `get_me`
- **THEN** her id, e-mail and display name equal those in the contract example

### Requirement: Safe to repeat
Running the command again SHALL leave exactly one copy of the demo data and SHALL NOT touch any other account.

#### Scenario: Second run
- **WHEN** the command runs twice
- **THEN** the counts of accounts, groups and tasks are the same after both runs

#### Scenario: Other data untouched
- **WHEN** another account and group exist
- **THEN** the command changes nothing of them

### Requirement: Explicit database
The command SHALL print the database file it works on and SHALL refuse to run with debug off unless it is told to explicitly.

#### Scenario: Production mode
- **WHEN** debug is off and the confirmation flag is missing
- **THEN** the command stops with a message and changes nothing
