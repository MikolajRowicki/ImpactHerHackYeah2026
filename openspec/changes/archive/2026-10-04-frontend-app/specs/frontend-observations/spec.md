# Spec Delta

## Purpose

Lets a partner or supporter answer short, closed questions about the mother's daily life, so the
summary can notice changes, without free text and without their answers ever being shown back.

## ADDED Requirements

### Requirement: Closed questions
A partner or supporter SHALL see the observation questions with their ready-made answers as labelled single choices, and no free-text field.

#### Scenario: Questions shown
- **WHEN** a supporter opens the questions screen
- **THEN** every question is shown with its answer options and no text field

#### Scenario: Care framing
- **WHEN** the questions screen is shown
- **THEN** a note says the answers are never shown one by one or with the author's name

### Requirement: Sending answers
The frontend SHALL send only the questions that were answered and SHALL require at least one answer.

#### Scenario: Partial answers
- **WHEN** a partner answers two of three questions and sends
- **THEN** the two answers are sent and a thank-you screen is shown

#### Scenario: Nothing answered
- **WHEN** a partner sends without any answer
- **THEN** a message asks for at least one answer and nothing is sent

### Requirement: Answers are not shown back
After sending, the frontend SHALL NOT show the given answers again on any screen.

#### Scenario: After the thank-you
- **WHEN** the thank-you screen is shown and the person opens the questions again
- **THEN** all choices are empty
