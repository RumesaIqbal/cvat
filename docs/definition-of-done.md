# Definition of Done

Written 6 October 2026, **before any feature code**, as required by §5.4.
Ticked at the end, each line carrying a number or a link. A tick with no evidence
beside it counts as unticked, so the evidence column is not optional.

## Floor — §3 items 1 to 4

- [ ] Endpoint returns the number of annotations per class for a task, read from the database
- [ ] Count is correct against a known task: task 1 must report **41,866** total and **person 12,451**
- [ ] A page in the web interface calls the endpoint
- [ ] The counts are shown as a graph
- [ ] The no-data case renders cleanly
- [ ] The failed-request case renders cleanly

## Login and access — §3 item 5

- [ ] The endpoint uses CVAT's existing login, with no separate account system
- [ ] A request with no login is refused, and the refusal is shown
- [ ] A logged-in user without access to that task is refused, and the refusal is shown

## Speed — §3 item 6

- [ ] One target, written down before measuring: MO-1, median of 5 runs ≤ 500 ms
- [ ] Measured 5 times, raw output saved
- [ ] Median and spread reported, not a single number
- [ ] Result is either met, or missed with the reason written down

## Grouping — §3 item 7

- [ ] One grouping beyond the plain count
- [ ] Why I chose it, written down next to it

## Live updates — §3 items 8 and 9

- [ ] The graph updates over WebSocket when annotations change
- [ ] The page recovers when the connection drops and comes back

## Decision record — §3 item 10

- [ ] Approach taken, approach rejected, and what the rejection cost, inside `docs/plan.md`

## Documents and process — §5

- [ ] `docs/plan.md` committed before any code
- [ ] `docs/objectives.md` states CPU, RAM, operating system and the cloned CVAT commit SHA
- [ ] This file exists, written before the work started
- [ ] Commits are incremental, not one large commit at the end
- [ ] Commit messages say what changed and why
- [ ] Everything I did not finish is listed in the section below

## Submission — §10

- [ ] Branch `dev-test01` pushed to my own fork
- [ ] One pull request, `dev-test01` → `develop` of my fork, and not against `cvat-ai/cvat`
- [ ] Loom recording, 5 minutes or less
- [ ] Pull request link and Loom link sent

## Not finished

_To be filled in at the end. Whatever did not make it goes here rather than quietly
disappearing — §8 gives partial credit for incomplete work I declare, and nothing
for incomplete work I hide._
