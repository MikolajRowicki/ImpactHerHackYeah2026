# ai-provider-config Specification

## Purpose
Makes the AI provider and every secret come from the environment, so the demo can run on a mock and later switch to a real provider by changing one variable.

## Requirements

### Requirement: Provider is chosen by environment
The application SHALL pick the AI provider from the `AI_PROVIDER` variable. The default, when the variable is unset, SHALL be `mock`.

#### Scenario: Default provider
- **WHEN** the application starts and `AI_PROVIDER` is unset
- **THEN** the mock provider is used

#### Scenario: Explicit mock
- **WHEN** `AI_PROVIDER=mock`
- **THEN** the mock provider is used and no key is needed

### Requirement: Mock provider is deterministic
The mock provider SHALL return the same text for the same input and SHALL work without network access.

#### Scenario: Repeated call
- **WHEN** the mock provider is called twice with the same input
- **THEN** both calls return identical text

#### Scenario: Mock is labelled
- **WHEN** a response comes from the mock provider
- **THEN** the response reports its source as a mock, so that mock text is never shown as real model output

### Requirement: Bad provider configuration fails at startup
The application SHALL refuse to start when `AI_PROVIDER` holds a value that is not available.

#### Scenario: Unknown value
- **WHEN** `AI_PROVIDER` is set to an unknown name
- **THEN** startup stops with a message that lists the available values

### Requirement: Secrets come from the environment
The application SHALL read every secret from the environment, SHALL stop at startup when the Django secret key is missing and debug is off, and the repository SHALL contain `.env.example` listing every variable with no real values.

#### Scenario: Missing secret key in production mode
- **WHEN** debug is off and the secret key variable is empty
- **THEN** startup stops with a message naming the missing variable

#### Scenario: Example file is complete
- **WHEN** the variables read by the settings are compared with the names in `.env.example`
- **THEN** every variable appears in `.env.example`

### Requirement: Groq provider
When `AI_PROVIDER=groq`, the application SHALL generate texts through Groq with the key from `GROQ_API_KEY`, and the response source SHALL be `groq`. Startup SHALL stop with a message naming the variable when the key is missing.

#### Scenario: Missing key
- **WHEN** `AI_PROVIDER=groq` and `GROQ_API_KEY` is empty
- **THEN** startup stops with a message naming `GROQ_API_KEY`

#### Scenario: Available value
- **WHEN** the application starts with an unknown provider
- **THEN** the message lists `mock` and `groq`

#### Scenario: Real text is labelled
- **WHEN** Groq answers a request
- **THEN** the response source is `groq`

### Requirement: Provider failures never break a request
A provider call SHALL have a time limit of 8 seconds. An error, a timeout or an empty answer SHALL be reported to the caller of the provider as a failure, and the AI features SHALL answer with their fixed fallback.

#### Scenario: Timeout
- **WHEN** Groq does not answer within the limit
- **THEN** the feature returns its fallback and the request does not fail

#### Scenario: No network in tests
- **WHEN** the test suite runs
- **THEN** no test calls the real Groq service

### Requirement: Key stays secret
The key SHALL come only from the environment and SHALL NOT appear in logs, responses or error messages.

#### Scenario: Error text
- **WHEN** a Groq call fails
- **THEN** neither the log line nor the response contains the key
