# help-paths Specification

## Purpose
Shows where to get real help: crisis lines and a care path for each voivodeship. The app points to help and never replaces it.

## Requirements

### Requirement: Crisis lines
The API SHALL list crisis lines with name, number, hours and a short Polish description, always including the emergency number 112. Every entry SHALL carry a source link.

#### Scenario: Always available
- **WHEN** any signed-in person calls `get_help`
- **THEN** the response includes the emergency number 112 and at least one crisis line for emotional distress

#### Scenario: Sources
- **WHEN** the entries are listed
- **THEN** each has a source URL

### Requirement: Care path per voivodeship
The API SHALL return a care path for one of the 16 voivodeships: ordered steps from the first step to urgent help, and the regional contact of the national health fund. The voivodeship comes from the request or from the caller's saved preference.

#### Scenario: Requested voivodeship
- **WHEN** a client asks for a valid voivodeship
- **THEN** the response holds the path of that voivodeship

#### Scenario: Saved preference
- **WHEN** no voivodeship is requested and the caller saved one
- **THEN** the path of the saved voivodeship is returned

#### Scenario: Neither
- **WHEN** no voivodeship is requested or saved
- **THEN** the crisis lines and a general path are returned and `voivodeship` is null

#### Scenario: Unknown value
- **WHEN** the requested voivodeship is not one of the 16
- **THEN** the response is 422 with a message under `fields.voivodeship`

#### Scenario: Complete data
- **WHEN** the help data is checked
- **THEN** all 16 voivodeships have a path

### Requirement: No diagnosis
Help texts SHALL describe where to seek help and SHALL NOT state or suggest a diagnosis.

#### Scenario: Wording guard
- **WHEN** all help texts are scanned for diagnostic claims such as "you have depression"
- **THEN** none is found
