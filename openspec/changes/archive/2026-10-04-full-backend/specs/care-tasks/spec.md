# Spec Delta

## Purpose

Lets everyone in a group share care tasks: add them, take one, finish it or hand it back. Taking a task is safe when two people try at once.

## ADDED Requirements

### Requirement: Listing tasks
Every member, the woman included, SHALL see all tasks of their group, open tasks first.

#### Scenario: Order
- **WHEN** a member lists tasks that are open, claimed and done
- **THEN** open tasks come first, then claimed, then done, each newest first

#### Scenario: Other group
- **WHEN** a member lists tasks
- **THEN** no task of another group appears

### Requirement: Adding a task
Any member of an active group SHALL add a task with a title of 1 to 120 characters and optional details up to 500. The task starts open.

#### Scenario: Valid task
- **WHEN** a member posts a title
- **THEN** the response is 201, the status is `open`, `claimed_by` is null and `created_by` is the caller

#### Scenario: Invalid
- **WHEN** the title is empty or longer than 120 characters
- **THEN** the response is 422 with a message under `fields.title`

#### Scenario: Group not active
- **WHEN** a member posts a task in a pending or closed group
- **THEN** the response is 409 with code `group_pending` or `group_closed`

### Requirement: Claiming is atomic
A member SHALL claim an open task. Two simultaneous claims SHALL produce one winner and one refusal, and never two owners.

#### Scenario: Claim
- **WHEN** a member claims an open task
- **THEN** the response is 200, the status is `claimed` and `claimed_by` is the caller

#### Scenario: Race
- **WHEN** two members claim the same open task at once
- **THEN** one gets 200 and the other gets 409 with code `task_not_open`

#### Scenario: Claim twice
- **WHEN** a member claims a task that is already claimed or done
- **THEN** the response is 409 with code `task_not_open`

#### Scenario: Other group
- **WHEN** a member claims a task id of another group
- **THEN** the response is 404 with code `not_found`

### Requirement: Completing
Only the person who claimed a task SHALL complete it.

#### Scenario: Claimer completes
- **WHEN** the claimer completes a claimed task
- **THEN** the response is 200, the status is `done` and `completed_at` is set

#### Scenario: Someone else
- **WHEN** another member completes it
- **THEN** the response is 403 with code `not_task_claimer`

#### Scenario: Not claimed
- **WHEN** a member completes an open task
- **THEN** the response is 409 with code `task_not_claimed`

#### Scenario: Complete twice
- **WHEN** the claimer completes a done task
- **THEN** the response is 409 with code `task_not_claimed` and `completed_at` does not change

### Requirement: Releasing a task
The claimer SHALL hand a claimed task back, which makes it open again. A new operation provides this.

#### Scenario: Release
- **WHEN** the claimer releases a claimed task
- **THEN** the response is 200, the status is `open` and `claimed_by` is null

#### Scenario: Someone else
- **WHEN** another member releases it
- **THEN** the response is 403 with code `not_task_claimer`

#### Scenario: Done task
- **WHEN** the claimer releases a done task
- **THEN** the response is 409 with code `task_not_claimed`

### Requirement: Task suggestions
Members SHALL get a fixed list of ready-made care tasks in Polish to add with one action, such as a meal, a walk with the baby or an hour of sleep for her.

#### Scenario: List
- **WHEN** a member lists suggestions
- **THEN** each has a title and details that fit the task limits

### Requirement: Task integrity
A task SHALL never be `claimed` without a claimer, `open` with a claimer, or `done` without a completion time, enforced by the database.

#### Scenario: Constraint
- **WHEN** a row that breaks one of these rules is inserted directly
- **THEN** the database rejects it
