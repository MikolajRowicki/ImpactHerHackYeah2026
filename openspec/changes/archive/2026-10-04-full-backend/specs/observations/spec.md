# Spec Delta

## Purpose

Lets her partner and close ones answer short, closed, caring questions about her daily life. Answers feed the trend engine and are never shown one by one or with their author.

## ADDED Requirements

### Requirement: Closed questions
The API SHALL give partners and supporters a fixed list of questions with ready-made answers. The list SHALL cover facts about her life, for example going out, and emotions with special weight, for example sadness and crying. It SHALL hold no rating scale and no free text.

#### Scenario: List questions
- **WHEN** a partner or a supporter lists the questions
- **THEN** each question has an id, Polish text worded as care, and at least two answers of the allowed values

#### Scenario: Required topics
- **WHEN** the list is read
- **THEN** it contains a question about going out and questions about sadness and crying

#### Scenario: Woman cannot list
- **WHEN** the woman lists the questions
- **THEN** the response is 403 with code `forbidden`

### Requirement: Recording observations
A partner or a supporter of an active group SHALL answer one or more questions, each with one answer that the question offers. An observation is stored with its author for the trend engine only.

#### Scenario: Valid observation
- **WHEN** a supporter answers two known questions with offered answers
- **THEN** the response is 201 with an id and a UTC timestamp and nothing else

#### Scenario: Unknown question or answer
- **WHEN** a question id is unknown, an answer is not offered by that question, or the same question appears twice
- **THEN** the response is 422 with `fields` naming the problem

#### Scenario: Group not active
- **WHEN** a partner answers in a pending or closed group
- **THEN** the response is 409 with code `group_pending` or `group_closed`

#### Scenario: Not the woman
- **WHEN** the woman posts an observation
- **THEN** the response is 403 with code `forbidden`

### Requirement: Answers are never shown one by one
No operation SHALL return a single observation answer, and none SHALL return who gave an answer, to any role, the woman included.

#### Scenario: No read path
- **WHEN** every operation response is searched for an observation answer value tied to a question id or an author
- **THEN** none is found

### Requirement: Answers leave with their author
When their author leaves, is removed or deletes the account, the answers SHALL be deleted and SHALL no longer count in the trend.

#### Scenario: Removal changes the trend
- **WHEN** the only observer is removed from a group that showed `needs_attention` because of their answers
- **THEN** the next summary no longer carries that signal
