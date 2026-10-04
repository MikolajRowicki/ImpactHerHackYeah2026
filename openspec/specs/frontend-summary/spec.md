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
The trend SHALL be shown as a short gentle sentence with an icon, never as a number, a score or a red, amber or green signal. A trend that needs attention SHALL point to the help place. The `uncertain` trend SHALL be worded so that it is true when there is too little data, and SHALL NOT claim that the last days were of any kind.

#### Scenario: Needs attention
- **WHEN** the summary trend is `needs_attention`
- **THEN** a gentle sentence and a link to the help place are shown, and no red colour is used

#### Scenario: Stable
- **WHEN** the summary trend is `stable`
- **THEN** a calm sentence is shown and no help prompt is added

#### Scenario: Uncertain with no data
- **WHEN** the summary trend is `uncertain` and the statements say there is too little information
- **THEN** the trend sentence does not say that the last days were different

### Requirement: Summary time
The summary SHALL show when it was prepared, in the person's local time.

#### Scenario: Generated time
- **WHEN** a summary is shown
- **THEN** its preparation time is shown as a local date and time

### Requirement: Sample narrative is hidden
The frontend SHALL NOT show a narrative whose source is `mock`, and SHALL show no sample label.

#### Scenario: Mock narrative
- **WHEN** the summary narrative has source `mock`
- **THEN** no narrative text and no "sample text" label are shown

#### Scenario: Real narrative
- **WHEN** the summary narrative has source `rules` or `ai`
- **THEN** its text is shown

### Requirement: Reasons and help with the summary
The start screens SHALL read the extended summary. When it carries reasons, they SHALL be shown under the trend as a general explanation. When it carries help, the crisis lines SHALL be shown with the summary.

#### Scenario: Needs attention with help
- **WHEN** the extended summary has trend `needs_attention`, reasons and help
- **THEN** the reasons and the crisis lines are shown with the summary

#### Scenario: Stable
- **WHEN** the extended summary has no help
- **THEN** no crisis lines are shown
