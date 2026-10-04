# frontend-landing Specification

## Purpose
TBD - created by archiving change user-flow-and-groups. Update Purpose after archive.

## Requirements

### Requirement: Landing page for visitors
A signed-out visitor opening the app SHALL see a landing page, not the sign-in form. It SHALL say what the app is, show the three roles (mother, partner, close person), explain how it works in a few steps, state the privacy promise (her own entries stay private, loved ones see only a general picture), and offer sign-up and sign-in. It SHALL state that the app does not diagnose and link to the help place.

#### Scenario: Visitor sees the landing page
- **WHEN** a signed-out visitor opens the app root
- **THEN** the landing page is shown with a sign-up and a sign-in action

#### Scenario: Roles explained
- **WHEN** the landing page is shown
- **THEN** it describes the mother, the partner and the close person in separate blocks

#### Scenario: Signed in
- **WHEN** a signed-in person opens the app root
- **THEN** their start is shown, not the landing page

#### Scenario: Invitation links still work
- **WHEN** a signed-out visitor opens an invitation link
- **THEN** the invitation screen is shown, not the landing page

### Requirement: Calm motion and accessibility
Motion on the landing page SHALL be subtle, SHALL NOT be needed to read anything, and SHALL be off when the person prefers reduced motion. The page SHALL work on phone and laptop in both themes, with at least 4.5:1 text contrast.

#### Scenario: Reduced motion
- **WHEN** the system prefers reduced motion
- **THEN** no element animates and all content is visible at once

#### Scenario: Phone width
- **WHEN** the landing page is shown at 375 px width
- **THEN** it has no horizontal scroll

#### Scenario: Both themes
- **WHEN** the landing page is shown in light and dark themes
- **THEN** its body text meets the contrast ratio
