# Spec Delta

## Purpose

Lets a person create an account, sign in with a session, see who they are and delete their data. Defines how the running API reports errors, so every client sees the shape the contract promises.

## ADDED Requirements

### Requirement: Registration
The API SHALL create an account from an e-mail, a password and a display name, start a session and return the person with `membership: null`. E-mail addresses are unique regardless of letter case.

#### Scenario: Successful registration
- **WHEN** a client posts a valid e-mail, a password of 8 to 128 characters and a display name of 1 to 60 characters
- **THEN** the response is 201 with the person, `membership` is null and the session cookie is set

#### Scenario: Duplicate e-mail
- **WHEN** a client registers an e-mail that exists, in any letter case
- **THEN** the response is 422 with a message under `fields.email` and no second account exists

#### Scenario: Invalid fields
- **WHEN** the e-mail is malformed, the password is shorter than 8 characters or the display name is empty
- **THEN** the response is 422 with a Polish message per offending field in `fields`

### Requirement: Sign in and sign out
The API SHALL start a session for a correct e-mail and password and end it on sign-out. A wrong e-mail and a wrong password SHALL give the same answer.

#### Scenario: Correct credentials
- **WHEN** a client posts a registered e-mail and its password
- **THEN** the response is 200 with the person and a session cookie

#### Scenario: Wrong credentials
- **WHEN** the e-mail is unknown or the password is wrong
- **THEN** the response is 401 with code `invalid_credentials` and the same message in both cases

#### Scenario: Sign out
- **WHEN** a signed-in client signs out and then calls `get_me`
- **THEN** sign-out answers 200 and `get_me` answers 401

### Requirement: Current person
The API SHALL return the signed-in person with their membership: group id, role and group status, or null when they have no group.

#### Scenario: Person without a group
- **WHEN** a person with no group calls `get_me`
- **THEN** the response is 200 with `membership` null

#### Scenario: Person in a group
- **WHEN** a member calls `get_me`
- **THEN** the response carries their group id, their role and the group status

### Requirement: Protected operations need a session
Every operation other than `health`, `register`, `login` and `get_invitation` SHALL answer 401 with code `unauthorized` when called without a valid session.

#### Scenario: No session
- **WHEN** a client calls any protected operation without a session
- **THEN** the response is 401 with the common error shape

### Requirement: CSRF protection
Unsafe methods SHALL require the `X-CSRFToken` header that matches the `csrftoken` cookie.

#### Scenario: Missing token
- **WHEN** a signed-in client sends a POST or DELETE without the header
- **THEN** the request is refused and nothing changes

### Requirement: Uniform errors from the running API
Every error the running API produces under `/api/v1`, including unknown paths, wrong methods and malformed JSON, SHALL have the common error shape with a stable code and a Polish message.

#### Scenario: Unknown path
- **WHEN** a client calls a path under `/api/v1` that does not exist
- **THEN** the response is 404 with code `not_found` in the common error shape

#### Scenario: Malformed body
- **WHEN** a client sends a body that is not valid JSON
- **THEN** the response is 422 with code `validation_error` in the common error shape

#### Scenario: Unexpected failure
- **WHEN** a request fails with an unexpected server error
- **THEN** the response is 500 with code `server_error` in the common error shape and no internal detail

### Requirement: Account deletion
The API SHALL delete the signed-in person's account and everything they wrote, end the session and answer 200. When the person is the woman of a group, the whole group and its data are deleted with her.

#### Scenario: Supporter deletes the account
- **WHEN** a supporter calls `delete_account`
- **THEN** their account, membership and observation answers are gone, tasks they claimed become open again, and the group keeps working

#### Scenario: Woman deletes the account
- **WHEN** the woman calls `delete_account`
- **THEN** the group, its members' memberships, check-ins, observations, tasks and invitations are deleted, and the other members have no group

#### Scenario: Session ends
- **WHEN** an account is deleted
- **THEN** the same session cookie answers 401 afterwards

### Requirement: Personal preferences
A person SHALL read and save their preferences: the voivodeship used for help paths (one of the 16, or none) and the e-mail reminder switch.

#### Scenario: Defaults
- **WHEN** a person who saved nothing reads preferences
- **THEN** the voivodeship is null and e-mail reminders are on

#### Scenario: Save
- **WHEN** a person saves a valid voivodeship
- **THEN** reading preferences returns it

#### Scenario: Unknown voivodeship
- **WHEN** the value is not one of the 16
- **THEN** the response is 422 with a message under `fields.voivodeship`
