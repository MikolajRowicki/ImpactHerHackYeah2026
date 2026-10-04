# ai-assist Specification

## Purpose
Gives two optional helpers that use text generation: one helps the woman say something hard to her close ones, the other helps her close ones start a caring conversation with cited sources. Every answer says where its text came from and is safe when the provider fails.

## Requirements

### Requirement: Say it for me
The woman SHALL send what she wants to say, who it is for (partner or supporters) and a tone (`gentle` or `direct`) and receive a short suggested message she can copy. The text she sends SHALL NOT be stored or logged.

#### Scenario: Suggestion
- **WHEN** the woman posts a text of 1 to 500 characters, a recipient and a tone
- **THEN** the response is 200 with a `message`, a `source` and an empty `sources` list

#### Scenario: Not stored
- **WHEN** the request is handled
- **THEN** no table row and no log line contains her text

#### Scenario: Invalid
- **WHEN** the text is empty or longer than 500 characters, or the recipient or tone is unknown
- **THEN** the response is 422 with a message per field

#### Scenario: Only the woman
- **WHEN** a partner or a supporter calls it
- **THEN** the response is 403 with code `forbidden`

### Requirement: Crisis check comes first
Before any provider is called, the text of "say it for me" SHALL be checked by fixed rules for words that signal a crisis. A match SHALL return `crisis: true`, the help block and no generated message.

#### Scenario: Crisis words
- **WHEN** the text contains a phrase of the crisis list
- **THEN** the response has `crisis: true`, `message` null, the crisis lines and `source: "rules"`, and the provider is not called

#### Scenario: Ordinary text
- **WHEN** the text has no such phrase
- **THEN** `crisis` is false and the provider is used

### Requirement: Conversation guide
A partner or a supporter SHALL ask for a guide on a topic from a fixed set and receive suggested opening lines, things to avoid and follow-up questions. The guide SHALL NOT use any answer or check-in as input.

#### Scenario: Guide for a topic
- **WHEN** a supporter asks for the topic `how_are_you`
- **THEN** the response has opening lines, things to avoid, questions, a `source` and an empty `sources` list

#### Scenario: Unknown topic
- **WHEN** the topic is not in the set
- **THEN** the response is 422 with a message under `fields.topic`

#### Scenario: Not the woman
- **WHEN** the woman asks for a guide
- **THEN** the response is 403 with code `forbidden`

#### Scenario: Topic for the trend
- **WHEN** the trend is `needs_attention`
- **THEN** a topic about suggesting professional help exists in the set and is available to everyone who may ask

### Requirement: Fixed fallback texts
Every AI operation SHALL have deterministic fallback texts. When the provider fails, times out or returns an empty text, the response SHALL be 200 with the fallback and the source of the fallback.

#### Scenario: Provider error
- **WHEN** the provider raises an error
- **THEN** the response is 200, the text is the fallback and `source` is `rules`

#### Scenario: Source never forged
- **WHEN** any AI response is returned
- **THEN** `source` names what produced the text and is never `groq` for a fallback

### Requirement: Mock is labelled everywhere
Text produced by the mock provider SHALL carry `source: "mock"` in every AI response and in the summary narrative.

#### Scenario: Default provider
- **WHEN** `AI_PROVIDER` is unset and a conversation guide is requested
- **THEN** the source is `mock`

### Requirement: Cited sources can be added later
Generation SHALL go through a knowledge-source step that returns passages with a title and a link, empty by default. The response `sources` list SHALL list the passages used, so a later retrieval feature needs no change to the response shape.

#### Scenario: Default
- **WHEN** no knowledge source is configured
- **THEN** `sources` is an empty list and the answer is generated as before

#### Scenario: A source is supplied
- **WHEN** a knowledge source returns two passages
- **THEN** the response `sources` lists both with title and link
