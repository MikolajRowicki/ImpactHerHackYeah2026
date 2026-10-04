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
- **THEN** the response has opening lines, things to avoid, questions, a `source` and the `sources` the knowledge source gave (one to three pages with the default curated source)

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

### Requirement: Cited sources come from a knowledge source
The conversation guide SHALL ask a knowledge source for passages that fit its topic and SHALL give their text to the provider. Each passage has a title and a link. The response `sources` list SHALL list the passages used. "Say it for me" and the summary narrative SHALL NOT ask the knowledge source, and the `sources` of "say it for me" SHALL stay empty.

#### Scenario: Default
- **WHEN** `KNOWLEDGE_SOURCE` is unset and a guide is requested
- **THEN** the curated source is asked and `sources` lists the passages it returned

#### Scenario: Switched off
- **WHEN** `KNOWLEDGE_SOURCE=none` and a guide is requested
- **THEN** `sources` is an empty list and the answer is generated as before

#### Scenario: A source is supplied
- **WHEN** a knowledge source returns two passages for a guide
- **THEN** the response `sources` lists both with title and link, and the prompt sent to the provider holds the text of both

#### Scenario: Her words are never a query
- **WHEN** a knowledge source is configured and the woman asks "say it for me"
- **THEN** the knowledge source is not asked and `sources` is an empty list

#### Scenario: Narrative cites nothing
- **WHEN** a knowledge source is configured and a summary is prepared
- **THEN** the knowledge source is not asked and the narrative prompt holds no passage

#### Scenario: Fallback cites nothing
- **WHEN** the provider fails while a guide is prepared
- **THEN** the guide has the fixed texts, `source` is `rules` and `sources` is an empty list

#### Scenario: Broken source
- **WHEN** the knowledge source fails while a guide is prepared
- **THEN** the guide is still answered, with an empty `sources` list

### Requirement: Curated knowledge source
With `KNOWLEDGE_SOURCE=curated`, which is the default, passages SHALL come from a reviewed file in the repository. A lookup SHALL return at most three passages that match the topic or the keywords of the query, best match first, each from a different page, and an empty list when nothing matches. Case and Polish diacritics SHALL NOT affect matching.

#### Scenario: Every topic is covered
- **WHEN** a guide is requested with the curated source for any of the five topics
- **THEN** its `sources` list holds one to three entries, each with a title and an `https` link

#### Scenario: At most three, best first
- **WHEN** a query matches more than three passages
- **THEN** three passages are returned, and a passage tagged with the topic of the query comes before one that matches only by keywords

#### Scenario: Different pages
- **WHEN** two matching passages come from the same page
- **THEN** only the better of the two is returned and the next passage from another page takes the free place

#### Scenario: Any word form
- **WHEN** a query holds "Lekarzem" and a passage has the keyword "lekarz", or a query holds "pomóc" and a passage has the keyword "pomoc"
- **THEN** that passage is found

#### Scenario: No match
- **WHEN** a query matches no topic and no keyword
- **THEN** the list is empty

### Requirement: Opening lines do not show the speaker's gender
The guide SHALL drop a generated opening line that shows the speaker's gender: a first-person past, conditional or compound future form ("myślałem", "chciałbym", "żebym w ten weekend mógł", "będę pomagał") or a common adjective about oneself ("jestem z Ciebie dumny", "sam nie wiem"). Lines that speak to the mother ("zrobiłaś", "żebyś mogła") SHALL stay. When no generated line is left, the guide SHALL answer with its fixed opening lines, `source` `rules` and an empty `sources` list.

#### Scenario: One gendered line
- **WHEN** the provider writes three lines and one of them holds "chciałbym"
- **THEN** the guide shows the other two lines

#### Scenario: Other gendered forms
- **WHEN** a generated line holds "żebym pomógł", "będę Ci pomagał" or "jestem gotowa"
- **THEN** that line is dropped

#### Scenario: Lines to the mother stay
- **WHEN** a generated line holds "zrobiłaś", "żebyś mogła" or a noun such as "z pomysłem"
- **THEN** that line is shown

#### Scenario: Only gendered lines
- **WHEN** every generated line holds such a form
- **THEN** the guide has the fixed opening lines, `source` `rules` and no sources

### Requirement: Passages are well formed
Every passage in the curated file SHALL have a unique id, a title, an `https` link to a public page, a short text of at most 400 characters, at least one keyword, and topics only from the guide's set. Every guide topic SHALL have at least one passage.

#### Scenario: File check
- **WHEN** the curated file is read
- **THEN** every passage meets these rules and every topic has a passage
