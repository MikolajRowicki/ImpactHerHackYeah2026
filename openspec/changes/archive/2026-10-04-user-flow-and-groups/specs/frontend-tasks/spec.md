## ADDED Requirements

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
