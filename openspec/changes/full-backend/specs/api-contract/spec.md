# Spec Delta

## ADDED Requirements

### Requirement: Existing operations are frozen
The 25 operations of the v0 contract, their schemas, their error codes and their examples SHALL NOT change after this change. New behaviour arrives as new operations or new schemas. A committed baseline records the v0 content.

#### Scenario: Baseline guard
- **WHEN** an operation, schema or example listed in the baseline is changed or removed
- **THEN** the guard test fails and names it

#### Scenario: Additions allowed
- **WHEN** a new operation, schema or example is added
- **THEN** the guard test passes

### Requirement: New operations are declared like the old ones
Every new operation SHALL have an `operationId`, `x-roles`, error responses in the common shape and examples for each declared status, and SHALL pass the same guard tests as the v0 operations.

#### Scenario: Declared and exemplified
- **WHEN** the contract guard tests run
- **THEN** each new operation has its roles, its examples and valid schemas

### Requirement: Real responses match the contract
The test suite SHALL validate the status and body of real backend responses against the contract schemas for every operation and every declared status the backend can produce.

#### Scenario: Response drift
- **WHEN** the backend returns a field the schema does not allow, or omits a required one
- **THEN** a test fails

#### Scenario: Coverage
- **WHEN** operations are compared with those exercised by the response-validation tests
- **THEN** every operation is exercised at least once with its success status

### Requirement: Regression journeys
The test suite SHALL keep end-to-end journeys that run only v0 operations, and they SHALL stay green after every later change.

#### Scenario: Core journey
- **WHEN** a journey registers three people, creates a group, invites, accepts, records a check-in and an observation, reads the summary, and runs a task from creation to completion
- **THEN** every step returns the status and shape the v0 contract declares

#### Scenario: Partner-first journey
- **WHEN** a partner creates a pending group and the woman accepts
- **THEN** the group is empty until she accepts and active afterwards
