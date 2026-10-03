# Spec Delta

## Purpose

Turns the woman's check-ins and the answers of her close ones into one explainable trend and a gentle summary worded for each reader. The engine is plain rules; it never diagnoses and never uses AI to decide.

## ADDED Requirements

### Requirement: Trend from plain rules
The trend SHALL be computed from the data of the last 7 days (calendar days in Europe/Warsaw) by fixed rules. A signal day for the woman is a day with a check-in of mood `low` or `very_low`, or anxiety `strong`. A signal day for observations is a day with answer `more_than_usual` for sadness or `yes` for crying. The trend is `needs_attention` when any holds: the woman has 3 or more signal days; observations have 3 or more signal days; the woman and observations each have 2 or more; or a check-in of the last 2 days has mood `very_low` with anxiety `strong`. It is `stable` when data exists on 3 or more days and it is not `needs_attention` and there is at most 1 signal day in all. Otherwise it is `uncertain`.

#### Scenario: Too little data
- **WHEN** a group has data on fewer than 3 days in the window
- **THEN** the trend is `uncertain` unless a `needs_attention` rule holds

#### Scenario: Three hard days
- **WHEN** the woman has check-ins with `low` mood on 3 different days of the last 7
- **THEN** the trend is `needs_attention`

#### Scenario: Both sources agree
- **WHEN** the woman has 2 signal days and observations have 2 signal days
- **THEN** the trend is `needs_attention`

#### Scenario: Acute combination
- **WHEN** a check-in of yesterday has mood `very_low` and anxiety `strong`
- **THEN** the trend is `needs_attention` even with no other data

#### Scenario: Calm week
- **WHEN** data exists on 4 days and only 1 is a signal day
- **THEN** the trend is `stable`

#### Scenario: Old data does not count
- **WHEN** all signal days are older than 7 days
- **THEN** they do not influence the trend

#### Scenario: Removed observer
- **WHEN** an observer's answers are deleted
- **THEN** the trend is computed again without them

### Requirement: Summary for the caller's role
The API SHALL return a summary for the caller: audience, trend, general statements in gentle Polish, a care reminder, a narrative with its source and a UTC timestamp. The care reminder is a text for a partner or a supporter and null for the woman.

#### Scenario: Woman's summary
- **WHEN** the woman calls `get_summary`
- **THEN** audience is `woman`, `care_reminder` is null and statements speak to her in the second person

#### Scenario: Loved one's summary
- **WHEN** a partner or a supporter calls `get_summary` in an active group
- **THEN** `care_reminder` is a non-empty text asking them to take special care of her, stronger when the trend is `needs_attention`

#### Scenario: Pending group
- **WHEN** a member of a pending group calls `get_summary`
- **THEN** the trend is `uncertain` and the statements say there is not enough information yet

#### Scenario: Closed group
- **WHEN** a partner or a supporter calls `get_summary` after the woman closed the group
- **THEN** the trend is `uncertain`, a statement says the group is closed and `care_reminder` is null

### Requirement: Summary never exposes answers or authors
Statements, reminders and the narrative SHALL be general. They SHALL NOT quote an answer, name an author, count how many people answered, or reveal which source produced a signal.

#### Scenario: Single observer
- **WHEN** only one supporter has answered and the trend is `needs_attention`
- **THEN** no text of the summary names them, counts them or quotes what they answered

#### Scenario: Statement allowlist
- **WHEN** every statement the engine can produce is listed
- **THEN** each comes from a fixed set of general sentences

### Requirement: Narrative source is honest
The narrative SHALL come from the configured AI provider, using only the trend label and the general statements as input. Its `source` SHALL name what produced the text. When the provider is unavailable the narrative SHALL come from fixed rule texts with source `rules`.

#### Scenario: Mock provider
- **WHEN** the provider is `mock`
- **THEN** the narrative source is `mock`

#### Scenario: Input limit
- **WHEN** a provider is called for the narrative
- **THEN** its input contains no check-in value, no answer and no name

#### Scenario: Provider fails
- **WHEN** the provider raises an error or times out
- **THEN** the summary is still 200 with a `rules` narrative

### Requirement: Extended summary
A new operation `get_summary_extended` SHALL return everything `get_summary` returns plus `reasons`, a list of general explanations of the trend, and `help`, which is null unless the trend is `needs_attention`. When present, `help` holds the crisis lines and the care path for the caller's voivodeship.

#### Scenario: Reasons are explainable
- **WHEN** the trend is `needs_attention`
- **THEN** `reasons` has at least one general sentence saying which kind of signal led to it, without naming a source person

#### Scenario: Help present
- **WHEN** the trend is `needs_attention`
- **THEN** `help` carries the crisis lines and a care path

#### Scenario: Help absent
- **WHEN** the trend is `stable` or `uncertain`
- **THEN** `help` is null

#### Scenario: Existing summary unchanged
- **WHEN** `get_summary` is called after this change
- **THEN** its response has exactly the fields it had before
