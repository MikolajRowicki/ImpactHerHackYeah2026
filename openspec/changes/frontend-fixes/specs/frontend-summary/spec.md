## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Sample narrative is labelled
**Reason**: A sample text must not be shown to people at all.
**Migration**: A narrative with source `mock` is hidden instead of labelled.

## ADDED Requirements

### Requirement: Sample narrative is hidden
The frontend SHALL NOT show a narrative whose source is `mock`, and SHALL show no sample label.

#### Scenario: Mock narrative
- **WHEN** the summary narrative has source `mock`
- **THEN** no narrative text and no "sample text" label are shown

#### Scenario: Real narrative
- **WHEN** the summary narrative has source `rules` or `ai`
- **THEN** its text is shown
