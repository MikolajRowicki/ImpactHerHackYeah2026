## REMOVED Requirements

### Requirement: Help place is always reachable
**Reason**: The help place no longer is a placeholder without contacts; it shows real ones.
**Migration**: Replaced by "Help is always reachable" below and by `frontend-help`.

## ADDED Requirements

### Requirement: Help is always reachable
Every screen SHALL offer a way to the help place, signed in or not. The help place SHALL NOT give medical advice. Its contacts come from the backend (see `frontend-help`).

#### Scenario: Help from any screen
- **WHEN** any screen is shown, signed in or not
- **THEN** a link to the help place is visible and opens it

#### Scenario: Signed out
- **WHEN** a signed-out person opens the help place
- **THEN** it shows the emergency number 112 and a calm note that more help is available after signing in
