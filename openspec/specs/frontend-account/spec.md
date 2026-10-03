# frontend-account Specification

## Purpose
Lets people create an account, sign in and sign out of MaydayMama, and keeps signed-out people
away from screens that need a session.

## Requirements

### Requirement: Sign in
The frontend SHALL offer a sign-in form with e-mail and password and SHALL take the person to their start screen after a successful sign-in.

#### Scenario: Successful sign-in
- **WHEN** a person submits a correct e-mail and password
- **THEN** their start screen is shown with their name

#### Scenario: Wrong credentials
- **WHEN** the sign-in answers 401 `invalid_credentials`
- **THEN** the error message is shown above the form and the entered e-mail stays in its field

### Requirement: Register
The frontend SHALL offer a registration form with name, e-mail and password, SHALL check a password length of at least 8 characters before sending, and SHALL show field messages from a 422 answer next to their fields.

#### Scenario: Successful registration
- **WHEN** a person submits a valid name, e-mail and password
- **THEN** they are signed in and see the screen for starting or joining a group

#### Scenario: Short password
- **WHEN** a person enters a password shorter than 8 characters and submits
- **THEN** a message next to the password field explains the minimum and nothing is sent

#### Scenario: Server field errors
- **WHEN** registration answers 422 with field messages
- **THEN** each message is shown next to its field and the field is marked invalid

### Requirement: Sign out
The frontend SHALL let a signed-in person sign out from the app frame and SHALL show the sign-in screen afterwards.

#### Scenario: Sign out
- **WHEN** a signed-in person chooses to sign out
- **THEN** the sign-in screen is shown and the navigation no longer shows group sections

### Requirement: Signed-out redirect
When the current person call answers 401, the frontend SHALL show the sign-in screen and, after signing in, SHALL return to the address the person wanted.

#### Scenario: Invitation link while signed out
- **WHEN** a signed-out person opens an invitation link and then signs in
- **THEN** the invitation screen is shown again
