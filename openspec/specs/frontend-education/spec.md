# frontend-education Specification

## Purpose
TBD - created by archiving change user-flow-and-groups. Update Purpose after archive.

## Requirements

### Requirement: Education for everyone
Every signed-in person SHALL have an education place that needs no group. It SHALL explain in plain Polish what postpartum depression is and how it differs from the baby blues, which signs to notice, how a close person can support, and when and where to seek help. It SHALL name no diagnosis for a person and SHALL link to the help place.

#### Scenario: Open education
- **WHEN** a signed-in person without a group opens education
- **THEN** the sections are shown and a link to the help place is visible

#### Scenario: Same for every role
- **WHEN** a mother and a supporter open education
- **THEN** both see the same sections

#### Scenario: Not a diagnosis
- **WHEN** education is shown
- **THEN** a note says it is general information and not a diagnosis

### Requirement: Start for a person without a group
A signed-in person without a group SHALL see, besides the panel to start a group, an entry to education and to the help place.

#### Scenario: No group
- **WHEN** a person without a group opens the start
- **THEN** the panel, a link to education and a link to help are shown
