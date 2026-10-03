# frontend-summary Specification

## Purpose
Shows each member the general summary written for their role, in gentle words, without ever
showing a single answer, its author, a score or a traffic-light colour.

## Requirements

### Requirement: Summary on the start screen
Every member of an active group SHALL see the summary for their role on their start screen: its general statements and its narrative text.

#### Scenario: Mother's summary
- **WHEN** the mother opens her start screen
- **THEN** the statements and narrative of her summary are shown

#### Scenario: Loved one's summary with care reminder
- **WHEN** a partner opens the start screen and the summary has a care reminder
- **THEN** the care reminder is shown, set apart from the statements

### Requirement: Trend in gentle words
The trend SHALL be shown as a short gentle sentence with an icon, never as a number, a score or a red, amber or green signal. A trend that needs attention SHALL point to the help place.

#### Scenario: Needs attention
- **WHEN** the summary trend is `needs_attention`
- **THEN** a gentle sentence and a link to the help place are shown, and no red colour is used

#### Scenario: Stable
- **WHEN** the summary trend is `stable`
- **THEN** a calm sentence is shown and no help prompt is added

### Requirement: Sample narrative is labelled
A narrative with source `mock` SHALL carry a visible label that it is a sample text.

#### Scenario: Mock narrative
- **WHEN** the summary narrative has source `mock`
- **THEN** a "sample text" label is shown with it

### Requirement: Summary time
The summary SHALL show when it was prepared, in the person's local time.

#### Scenario: Generated time
- **WHEN** a summary is shown
- **THEN** its preparation time is shown as a local date and time
