# frontend-mock-mode Specification

## Purpose
Lets the frontend be built and shown without a running backend by serving the contract examples, so the two sides can progress on separate branches at the same time.

## Requirements

### Requirement: Mock mode serves contract examples
When mock mode is on, the frontend SHALL answer its API calls from the files in `contracts/examples/` and SHALL NOT send any request to the backend.

#### Scenario: Mock call
- **WHEN** the frontend opens its page with `?mock=1` and requests the current user
- **THEN** the data on screen comes from the matching example file and no network request goes to `/api/v1`

#### Scenario: Mock mode is remembered
- **WHEN** a person turned mock mode on and moves to another screen of the app
- **THEN** mock mode stays on until it is turned off with `?mock=0`

### Requirement: Mock mode is visible
While mock mode is on, the frontend SHALL show a persistent notice that the data is sample data.

#### Scenario: Notice on every screen
- **WHEN** mock mode is on and any screen is shown
- **THEN** the notice is visible on that screen

#### Scenario: No notice in live mode
- **WHEN** mock mode is off
- **THEN** no notice is shown

### Requirement: Live mode uses the same origin
When mock mode is off, the frontend SHALL call the API on its own origin, send the session cookie, and send the CSRF header on unsafe methods.

#### Scenario: Unsafe request
- **WHEN** the frontend sends a POST in live mode
- **THEN** the request carries the CSRF header

### Requirement: Frontend runs without a build step
The frontend SHALL consist of plain HTML, CSS and JavaScript files that a static file server can serve, and SHALL show the same page in a phone-sized and a laptop-sized window without horizontal scrolling.

#### Scenario: Static serving
- **WHEN** the repository root is served by a plain static file server and the frontend page is opened with `?mock=1`
- **THEN** the page loads and shows sample data

#### Scenario: Phone width
- **WHEN** the page is shown in a 375 pixel wide window
- **THEN** it has no horizontal scrollbar

### Requirement: Demo changes stay visible
In mock mode, changes the person makes SHALL be reflected on screen for the rest of the browser tab session: a saved check-in, an added, taken or finished task, a started or closed group, a removed member, signing in and out. No request SHALL go to the backend.

#### Scenario: Task taken in the demo
- **WHEN** in mock mode a person takes an open task and reloads the page
- **THEN** the task is still shown as taken by them and no request went to `/api/v1`

#### Scenario: Reset the demo
- **WHEN** the person presses the demo reset button
- **THEN** the screens show the contract examples again

### Requirement: Demo perspective switch
In mock mode, the notice SHALL offer a switch between the perspectives mother, partner, supporter, no group and pending group, and SHALL show the app as that person.

#### Scenario: Switch to partner
- **WHEN** the person picks the partner perspective in the mock notice
- **THEN** the start screen of the partner Piotr with his summary is shown

#### Scenario: No switch in live mode
- **WHEN** mock mode is off
- **THEN** no perspective switch is shown
