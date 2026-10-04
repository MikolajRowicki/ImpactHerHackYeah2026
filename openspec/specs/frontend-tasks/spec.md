# frontend-tasks Specification

## Purpose
Lets the group share the everyday load around the mother: add care tasks, take one on, and mark
it done, with no grading of anyone.

## Requirements

### Requirement: Task list
Every member of an active group SHALL see the tasks grouped as open, taken and done, each with its title, details, who added it and who took it.

#### Scenario: Grouped list
- **WHEN** a member opens the tasks screen
- **THEN** open, taken and done tasks are shown under their own headings with who added and who took them

#### Scenario: Empty list
- **WHEN** there are no tasks
- **THEN** a gentle empty state invites adding the first one

### Requirement: Add a task
A member SHALL be able to add a task with a title of 1 to 120 characters and optional details of up to 500 characters.

#### Scenario: Adding
- **WHEN** a member adds a task with a title
- **THEN** it appears under open tasks

#### Scenario: Missing title
- **WHEN** a member submits without a title
- **THEN** a message next to the title field asks for one and nothing is sent

### Requirement: Take and finish a task
A member SHALL be able to take an open task; the person who took it SHALL be able to mark it done. Others SHALL NOT see a done control on a task taken by someone else.

#### Scenario: Taking
- **WHEN** a member takes an open task
- **THEN** it moves under taken tasks with their name

#### Scenario: Finishing
- **WHEN** the member who took a task marks it done
- **THEN** it moves under done tasks

#### Scenario: Someone else's task
- **WHEN** a member views a task taken by another person
- **THEN** no done control is shown for it

#### Scenario: Conflict
- **WHEN** taking answers 409 because someone took it first
- **THEN** the message from the error is shown and the list is reloaded

### Requirement: No grading
The tasks screen SHALL NOT show counts per person, rankings or any rating of helpers.

#### Scenario: No ranking
- **WHEN** the tasks screen is shown
- **THEN** no per-person count or ranking is visible

### Requirement: Ready-made task ideas
The tasks screen SHALL offer the ready-made suggestions of `list_task_suggestions` in an active group. Choosing one SHALL create that task with `create_task` using the suggestion's title and details.

#### Scenario: Suggestions shown
- **WHEN** a member opens the tasks screen of an active group
- **THEN** the suggestions are listed with their titles and details

#### Scenario: Add a suggestion
- **WHEN** the member chooses "Dodaj" on a suggestion
- **THEN** a task with that title appears in the open tasks and a confirmation is shown

#### Scenario: Pending group
- **WHEN** the group is pending
- **THEN** no suggestions are offered
