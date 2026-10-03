# Spec Delta

## Purpose

Lets a person prove they own an e-mail address, recover a forgotten password and change it, without the service ever revealing who has an account. Defines how mail leaves the application and how its volume is limited.

## ADDED Requirements

### Requirement: Sign-up with activation
The API SHALL create an inactive account from an e-mail, a password and a display name, and send a link that activates it. It SHALL NOT start a session. The answer SHALL be the same for a new address and for an address that already has an account.

#### Scenario: New address
- **WHEN** a client signs up with a valid new e-mail
- **THEN** the response is 202, an inactive account exists, no session is set and one activation e-mail is sent

#### Scenario: Existing address
- **WHEN** a client signs up with an e-mail that has an account
- **THEN** the response is byte for byte the same 202 and no second account exists

#### Scenario: Invalid fields
- **WHEN** a field fails validation (malformed e-mail, short password, empty name)
- **THEN** the response is 422 with a Polish message per field

### Requirement: Activation
The API SHALL activate an account from the token in its link. A token is valid for 3 days and works once.

#### Scenario: Valid token
- **WHEN** a client posts a valid token
- **THEN** the response is 200 and the person can sign in

#### Scenario: Used, expired or forged token
- **WHEN** the token was already used, is older than 3 days, or was altered
- **THEN** the response is 404 with code `token_invalid`, the same for each reason

### Requirement: Sign-in needs an active account
`login` SHALL refuse an inactive account with the same status, code and message as a wrong password.

#### Scenario: Inactive account
- **WHEN** a person who has not activated tries to sign in with the right password
- **THEN** the response is 401 with code `invalid_credentials`, equal to the answer for a wrong password, and its message names both possible causes

### Requirement: Resending the activation link
The API SHALL send a new link to an inactive account on request. The answer SHALL be the same for known, unknown, already active and throttled addresses.

#### Scenario: Identical answers
- **WHEN** a client asks for a link for an inactive address, an unknown address and an active address
- **THEN** the three responses are identical, and only the inactive address gets an e-mail

### Requirement: Password reset
The API SHALL send a reset link to a known active address, with the same answer for every address. The link works once and for 1 hour. Setting the new password SHALL end the person's other sessions.

#### Scenario: Request
- **WHEN** a client requests a reset for a known and for an unknown address
- **THEN** both responses are identical and only the known address gets an e-mail

#### Scenario: Confirm
- **WHEN** a client posts a valid token and a password of 8 to 128 characters
- **THEN** the response is 200, the new password works and the old one does not

#### Scenario: Token reuse or expiry
- **WHEN** the token was used, is older than 1 hour or was altered
- **THEN** the response is 404 with code `token_invalid`

#### Scenario: Sessions end
- **WHEN** a password reset is confirmed while the person has another session
- **THEN** that session answers 401 afterwards

#### Scenario: Weak password
- **WHEN** the new password is shorter than 8 characters
- **THEN** the response is 422 with a message under `fields.password` and the token still works

### Requirement: Changing the password
A signed-in person SHALL change their password by giving the current one and a new one. Their other sessions end and the current one continues.

#### Scenario: Correct current password
- **WHEN** the person posts the right current password and a valid new one
- **THEN** the response is 200 and the new password works

#### Scenario: Wrong current password
- **WHEN** the current password is wrong
- **THEN** the response is 422 with a message under `fields.current_password` and the password is unchanged

### Requirement: Mail delivery
All e-mail SHALL go through one service that sends through SMTP when `EMAIL_MODE=smtp` and writes to the console otherwise. It SHALL send after the database transaction has committed, SHALL never raise into a request, and SHALL log a person's id, never an address or a token.

#### Scenario: Mail server down
- **WHEN** the SMTP server cannot be reached while a person signs up
- **THEN** the response is the same 202, the failure is logged without the address, and the person can ask for a new link

#### Scenario: Misconfigured SMTP
- **WHEN** `EMAIL_MODE=smtp` and `EMAIL_USER` or `EMAIL_PASS` is empty
- **THEN** startup stops with a message naming the variable

#### Scenario: Default
- **WHEN** `EMAIL_MODE` is unset
- **THEN** mail is written to the console

#### Scenario: Link base
- **WHEN** a link is built
- **THEN** it starts with `APP_BASE_URL`

### Requirement: Mail limits
The service SHALL allow at most 1 e-mail per 60 seconds and 3 per hour per address and kind, and 200 per day for all addresses. A refused send SHALL be silent for the caller, and the response SHALL equal the response of a sent one.

#### Scenario: Per address
- **WHEN** a client asks for the same link twice within 60 seconds
- **THEN** one e-mail is sent and both responses are equal

#### Scenario: Global limit
- **WHEN** the daily total is reached
- **THEN** no further e-mail is sent that day, an error is logged and responses stay unchanged

#### Scenario: Limits survive a restart
- **WHEN** the application restarts between two requests
- **THEN** the limits still count the earlier sends

### Requirement: Legacy registration policy
The existing `register` operation SHALL keep working as before when `ALLOW_LEGACY_REGISTER` is on, and SHALL be refused through its declared 422 when it is off. The default is on when debug is on and off otherwise.

#### Scenario: Switch on
- **WHEN** the switch is on
- **THEN** `register` creates an active account and starts a session as before

#### Scenario: Switch off
- **WHEN** the switch is off
- **THEN** `register` answers 422 with a Polish message under `fields.email` pointing to sign-up with e-mail confirmation, and creates no account

### Requirement: Mail content
Every e-mail SHALL be in Polish and carry only what the person needs: the link, its validity and a note to ignore it if they did not ask. It SHALL hold no health data, no trend and no other member's name.

#### Scenario: Activation e-mail
- **WHEN** an activation e-mail is built
- **THEN** it holds the link and its validity and nothing about a group
