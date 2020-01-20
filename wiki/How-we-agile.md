We follow the Scrum framework for development. Scrum is a simple framework for effective team collaboration on complex products.

![Scrum Cycle](https://wac-cdn.atlassian.com/dam/jcr:709d95de-f4d4-4faf-aa9f-4bead10e888b/sprint_cycle-c.png?cdnVersion=742)

## Backlog
### User story

A user story describes a desired feature or bug fix (functional requirement) in narrative form. The format usually has a title, a reporter, an assignee, some descriptive text on how the features work or steps to reproduce the same bug, reference to other documents like screenshots, and acceptance criteria to measure whether tasks are completed. 

### Product backlog

Product backlog is an ordered list of tasks consisting of user stories, that need to be done by developers. Thus, the backlog is the source of tasks for every sprint. It is constantly reviewed, modified and re-prioritized to accommodate users' needs. 

### Sprint backlog

Sprint backlog is the list of items selected from the product backlog by the development team for implementation during the current sprint cycle. It is the goal that the team expects to achieve at the end of the sprint.

## Stand-up (Daily scrum)

The stand-up is a short discussion at 11:00 AM CST every day, where team members summarize their work yesterday and organize activities for the following day. Common questions to ask are:

* What did I do yesterday?
* What do I plan to do today?
* Is there any difficulty or blocker?

Stand-up keeps every team member informed of the progress and contribution from the others and helps spot potential blockers for development. The stand-up should be efficient and is not appropriate for problem-solving discussions. 

### Kanban board
Kanban board is an important tool to track the progress of work during stand-up (We use [Github Kanban](https://github.com/radiome-flow/radiome/projects/1)). There are four steps in the kanban board:

### Todo
Todo is a candidate list of tasks from the current Sprint backlog in a simplistic form. During stand-ups, a team member picks up a task based on his responsibility, task priority, personal interests, etc, making himself an assignee of the task. Then the task is active and moved to In progress.

### In progress
In progress indicates that a developer is actively working on the task and fully responsible for the delivery. If there is a task that requires multiple developers to coordinate, then it should be broken apart into smaller tasks.

### Review in progress
This status represents that the assignee has completed his task according to the acceptance criteria but it may involve other members to confirm the fact further, such as reviewing his pull requests, adding more tests or check whether the features work as designed. 

### Done
Tasks marked as Done are completed, meeting all criteria set by the team. Done tasks will eventually be removed from both the Kanban board and the sprint backlog in the next sprint review.

## Sprint Planning
Our team adopts one week as one sprint. The work to be performed during the current sprint is planned during this meeting by the entire development team on Friday. Specific user stories in high priority are added to this current sprint from the product backlog. A sprint planning meeting lasts no more than two hours. During the planning meeting, team members estimate expected dev hours of relevant tasks and add them to the sprint backlog unless there are no more available dev hours. 

## Sprint review & retrospective
A sprint review is held at the end of the Sprint to inspect the sprint goal and adjust the Product Backlog if needed. The development team demonstrates the work that it has “Done” and answers questions from attendees. The team also discusses what went well during the Sprint, what problems it ran into, how those problems were solved and what could be improved.