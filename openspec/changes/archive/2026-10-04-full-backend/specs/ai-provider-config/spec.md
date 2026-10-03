# Spec Delta

## ADDED Requirements

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
