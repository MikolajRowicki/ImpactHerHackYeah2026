# Spec Delta

## Purpose

Lets the mother put something hard into words with "say it for me", and lets her close ones prepare a caring conversation with a guide that shows the sources behind it.

## ADDED Requirements

### Requirement: Say it for me screen
The mother SHALL have a "Powiedz to za mnie" screen. On it she writes what she wants to say (1 to 500 characters), picks the recipient (partner or close people) and the tone (gentle or direct), and gets a suggested message.

#### Scenario: Suggestion
- **WHEN** the mother fills in the form and sends it
- **THEN** the suggested message is shown with a copy button and a button for another suggestion

#### Scenario: Copy
- **WHEN** she presses the copy button
- **THEN** the message is on the clipboard and a short confirmation is visible

#### Scenario: Edit before copying
- **WHEN** she changes a word in the suggested message and presses the copy button
- **THEN** the clipboard holds her edited text

#### Scenario: Empty text
- **WHEN** she sends the form with an empty text
- **THEN** a message under the text field says what is missing and no request is sent

#### Scenario: Length
- **WHEN** she types in the text field
- **THEN** a counter shows how many of the 500 characters are used, and the field takes no more than 500

#### Scenario: Another suggestion
- **WHEN** she asks for another suggestion
- **THEN** the same text, recipient and tone are sent again and the new message replaces the old one

#### Scenario: Nothing kept
- **WHEN** she leaves the screen and opens it again
- **THEN** the text field is empty and her text is in no browser storage

#### Scenario: Failure keeps her text
- **WHEN** the request fails
- **THEN** an error with a way to try again is shown and her text stays in the field

### Requirement: Crisis answer
When the answer to "say it for me" has `crisis: true`, the screen SHALL show no message and no copy button. It SHALL show a calm sentence, the crisis lines from the answer with dialable numbers, and a link to the help place.

#### Scenario: Crisis words
- **WHEN** the answer is a crisis answer
- **THEN** the crisis lines with their numbers and a link to the help place are shown, and no message or copy button

### Requirement: Conversation guide screen
A partner or a supporter SHALL have a "Jak z nią rozmawiać" screen with the five topics. Choosing a topic SHALL show its opening lines, things to avoid and follow-up questions under their own headings. Each topic SHALL have its own address.

#### Scenario: Pick a topic
- **WHEN** a supporter picks the topic about listening without advice
- **THEN** that topic's opening lines, things to avoid and questions are shown, and the topic is marked as chosen

#### Scenario: Topic address
- **WHEN** a partner opens the address of the professional-help topic
- **THEN** that topic's guide is shown

#### Scenario: Unknown topic address
- **WHEN** the address names a topic that does not exist
- **THEN** the topic list is shown with no guide and no request is sent

#### Scenario: Other opening lines
- **WHEN** they ask for other opening lines
- **THEN** the guide for the same topic is requested again and shown

### Requirement: Sources under the guide
When the guide has sources, the screen SHALL list them under a "Źródła" heading. Each source SHALL be a link with its title and its site name, and SHALL open in a new tab. When the guide has no sources, no sources heading SHALL be shown.

#### Scenario: With sources
- **WHEN** the guide has two sources
- **THEN** both titles are links to their addresses with the site name, and they open in a new tab

#### Scenario: Without sources
- **WHEN** the guide has no sources
- **THEN** no "Źródła" heading is shown

### Requirement: Generated text is labelled
Text from a model SHALL carry a short label saying it was prepared with the help of AI. When the guide used sources, the label SHALL point to them. Mock text SHALL be labelled as a sample. Fixed texts (source `rules`) SHALL carry no label.

#### Scenario: AI text
- **WHEN** an answer has source `groq`
- **THEN** "Przygotowane z pomocą AI" is shown with the text

#### Scenario: AI text with sources
- **WHEN** a guide has source `groq` and sources
- **THEN** the label also says the text is based on the sources below

#### Scenario: Mock text
- **WHEN** an answer has source `mock`
- **THEN** "Tekst przykładowy" is shown with the text

#### Scenario: Fixed text
- **WHEN** an answer has source `rules`
- **THEN** no AI label and no sample label are shown

#### Scenario: Summary narrative from a model
- **WHEN** the summary narrative has source `groq`
- **THEN** "Przygotowane z pomocą AI" is shown with the narrative

### Requirement: Who can open the screens
"Powiedz to za mnie" SHALL be open only to the mother of an active or closed group. The guide SHALL be open only to a partner or a supporter of an active or closed group. Anyone else SHALL see the calm "not for you" screen.

#### Scenario: Partner opens say it for me
- **WHEN** a partner opens the address of "Powiedz to za mnie"
- **THEN** the screen saying it is only for the mother is shown

#### Scenario: Mother opens the guide
- **WHEN** the mother opens the address of the guide
- **THEN** the screen saying it is for close ones is shown

#### Scenario: No group
- **WHEN** a signed-in person without a group opens either address
- **THEN** the screen saying a group is needed is shown

### Requirement: Entry points
The mother's start screen SHALL offer a card that opens "Powiedz to za mnie". The start screen of a partner or supporter SHALL offer a card that opens the guide. When the summary a loved one sees needs attention, it SHALL offer a link to the professional-help topic of the guide. The navigation SHALL NOT get new items.

#### Scenario: Mother's start
- **WHEN** the mother opens her start screen in an active group
- **THEN** a card leads to "Powiedz to za mnie"

#### Scenario: Loved one's start
- **WHEN** a supporter opens the start screen in an active group
- **THEN** a card leads to the guide

#### Scenario: Needs attention
- **WHEN** a partner's summary trend is `needs_attention`
- **THEN** a link opens the guide on suggesting professional help

#### Scenario: Mother's summary
- **WHEN** the mother's summary trend is `needs_attention`
- **THEN** no link to the guide is shown

#### Scenario: Navigation unchanged
- **WHEN** the mother or a loved one is signed in to an active group
- **THEN** the navigation offers the same items as before this change

### Requirement: Waiting for an answer
While an answer is on its way, the button that asked for it SHALL be disabled and SHALL say that the text is being prepared, so a second press sends nothing.

#### Scenario: Double press
- **WHEN** the mother presses the send button twice quickly
- **THEN** one request is sent

### Requirement: Mock mode answers both helpers
In mock mode, both helpers SHALL work without the backend. The mother gets a sample message for the chosen recipient and tone, crisis phrases give the crisis answer, and each topic gives its guide with sample sources.

#### Scenario: Mock suggestion
- **WHEN** mock mode is on and the mother sends the form
- **THEN** a sample message is shown and no request goes to `/api/v1`

#### Scenario: Mock crisis
- **WHEN** mock mode is on and she writes "nie chcę żyć"
- **THEN** the crisis lines are shown

#### Scenario: Mock guide
- **WHEN** mock mode is on and a partner picks a topic
- **THEN** the guide and its sources are shown
