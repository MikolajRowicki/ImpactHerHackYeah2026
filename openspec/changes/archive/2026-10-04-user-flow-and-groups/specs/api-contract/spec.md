## ADDED Requirements

### Requirement: Group selection convention
The contract SHALL describe the optional `X-Group-Id` request header as a convention for every group-bound operation, and SHALL declare `list_memberships` as a new operation with examples. No v0 operation, schema or example SHALL change.

#### Scenario: Convention documented
- **WHEN** the contract is read
- **THEN** the header, its default and its refusals are described in the conventions

#### Scenario: Baseline guard still holds
- **WHEN** the baseline guard test runs after this change
- **THEN** it passes
