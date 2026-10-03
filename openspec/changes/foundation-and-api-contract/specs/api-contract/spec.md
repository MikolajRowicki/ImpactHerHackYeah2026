# Spec Delta

## Purpose

Defines the written API contract that backend and frontend build against in parallel, so that neither side has to guess what the other does.

## ADDED Requirements

### Requirement: Contract is published and valid
The repository SHALL contain `contracts/openapi.yaml`, a valid OpenAPI document, and `contracts/examples/` with example request and response payloads for every operation.

#### Scenario: Document validates
- **WHEN** the contract document is checked with an OpenAPI validator
- **THEN** it reports no errors

#### Scenario: Examples match their schemas
- **WHEN** every example payload is validated against the schema of its operation
- **THEN** every example passes

#### Scenario: Every operation has an example
- **WHEN** the operations in the contract are compared with the files in `contracts/examples/`
- **THEN** each operation has at least one success example and each operation that can fail has at least one error example

### Requirement: Contract covers the v0 resources
The contract SHALL describe, under the `/api/v1` prefix, these resources: health, authentication and current user, group, members and invitations, check-ins, observations, summary, tasks, self-care suggestions.

#### Scenario: All resources are present
- **WHEN** the paths in the contract are listed
- **THEN** each resource named above has at least one path

### Requirement: Common API conventions
The API SHALL exchange JSON, authenticate with a session cookie plus a CSRF header on unsafe methods, and write every timestamp as ISO 8601 in UTC.

#### Scenario: Unauthenticated call
- **WHEN** a client calls a protected operation without a session
- **THEN** the contract declares a 401 response with the common error shape

#### Scenario: Timestamps
- **WHEN** a response schema contains a point in time
- **THEN** its format is a UTC date-time

### Requirement: Uniform error shape
Every error response SHALL have the body `{"error": {"code": <string>, "message": <string>, "fields": <object, optional>}}`, with `code` stable and machine readable and `message` in Polish for the user.

#### Scenario: Validation error
- **WHEN** a request body fails validation
- **THEN** the contract declares a 422 response with the common error shape and per-field messages in `fields`

#### Scenario: Forbidden by role
- **WHEN** a member calls an operation their role is not allowed to use
- **THEN** the contract declares a 403 response with the common error shape

### Requirement: Role permissions are part of the contract
The contract SHALL state, per operation, which group roles may call it. The woman owns the group; the partner and supporters are members with fewer rights.

#### Scenario: Only the woman invites outsiders
- **WHEN** the invitation operation is read
- **THEN** it allows the woman to invite any role, allows the partner to invite only the woman while the group is pending, and declares 403 for supporters

#### Scenario: Group is empty until she agrees
- **WHEN** a partner creates a group
- **THEN** the group status is `pending`, and no check-in, observation or task operation accepts data for it until the woman accepts the invitation

#### Scenario: Only the woman removes members
- **WHEN** the operation that removes a member or closes the group is read
- **THEN** it allows only the woman

### Requirement: Privacy rules are part of the contract
The contract SHALL keep the woman's own entries readable only by her, and SHALL expose no individual observation answers and no author of an answer to anyone through the summary.

#### Scenario: Her check-ins are private
- **WHEN** the check-in operations are read
- **THEN** the list and read operations allow only the woman, and no other operation returns a check-in

#### Scenario: Summary has no individual answers
- **WHEN** the summary response schema is read
- **THEN** it contains general statements and trend labels, and contains no field with a single answer or the author of an answer

#### Scenario: Observations are closed questions
- **WHEN** the observation request schema is read
- **THEN** every answer is one value from a fixed set, and no free-text field about the woman exists

### Requirement: Implemented routes are declared
The backend SHALL expose no `/api/v1` route that is missing from the contract.

#### Scenario: Undeclared route
- **WHEN** a route is added to the backend without a matching path and method in the contract
- **THEN** the contract guard test fails

### Requirement: Health endpoint
The backend SHALL answer `GET /api/v1/health` without authentication with status 200 and a JSON body that reports the service as running.

#### Scenario: Service is up
- **WHEN** a client calls `GET /api/v1/health`
- **THEN** the response is 200 and its body matches the contract example
