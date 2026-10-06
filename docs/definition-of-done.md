# Definition of Done

Written 6 October 2026, **before any feature code**, as required by §5.4.
Ticked at the end, each line carrying a number or a link. A tick with no evidence
beside it counts as unticked, so the evidence column is not optional.

## Floor — §3 items 1 to 4

- [x] Endpoint returns the number of annotations per class for a task, read from the database — `cvat/apps/test/` (`services.py`, `views.py`), commit `22d00f798`
- [x] Count is correct against a known task: task 1 must report **41,866** total and **person 12,451** — every raw measurement run returned `total 41866` (`docs/perf/annotation-stats.md`); label response verified as `person 12451` with 80 entries, and `source` view totals 41,866
- [x] A page in the web interface calls the endpoint — route `/tasks/:id/annotation-stats`, commit `8aa3f4e73`
- [x] The counts are shown as a graph — bar chart, commits `65a13f30a`, `d1c6eee7d`; entry point from the task page, commit `3c2139d7a`
- [x] The no-data case renders cleanly — empty-state `<Alert>` when `stats.total === 0`, commit `8aa3f4e73`
- [x] The failed-request case renders cleanly — `<Result status="error">` with message and retry, commit `8aa3f4e73`

## Login and access — §3 item 5

- [x] The endpoint uses CVAT's existing login, with no separate account system — DRF `SessionAuthentication` + `TokenAuthentication` list plus the anonymous curl matrix, all in commit `22d00f798`
- [x] A request with no login is refused, and the refusal is shown — anonymous request verified as HTTP 401; the page renders the failed-request state
- [x] A logged-in user without access to that task is refused, and the refusal is shown — user without task access verified as HTTP 403 through OPA/`TaskPermission`

## Speed — §3 item 6

- [x] One target, written down before measuring: MO-1, median of 5 runs ≤ 500 ms — `docs/objectives.md`, commit `d388d8ed7`
- [x] Measured 5 times, raw output saved — `scripts/measure-annotation-stats.ps1`, raw runs in `docs/perf/annotation-stats.md`, commit `a094aa7b2`
- [x] Median and spread reported, not a single number — median 444 ms, min 429 ms, max 606 ms, spread 177 ms (`docs/perf/annotation-stats.md`)
- [x] Result is either met, or missed with the reason written down — met; the 500 ms target and 1,000 ms ceiling are both cleared (median 444 ms, max 606 ms)

## Grouping — §3 item 7

- [x] One grouping beyond the plain count — `group_by=source`, commit `dca7f7673`
- [x] Why I chose it, written down next to it — rationale in `docs/plan.md`, step 6

## Live updates — §3 items 8 and 9

- [x] The graph updates over WebSocket when annotations change — pure-ASGI handler streaming recomputed counts, commit `4a36bc145`; handshake and auth close codes verified in a real browser (anonymous 4401, unknown route 4404, bad `group_by` 4400, missing task 4403)
- [x] The page recovers when the connection drops and comes back — client reconnect loop with capped exponential backoff (1 s × 2 up to 30 s) plus a full snapshot pushed on every successful connect, commit `4a36bc145`

## Decision record — §3 item 10

- [x] Approach taken, approach rejected, and what the rejection cost, inside `docs/plan.md` — see the two decision-record entries in `docs/plan.md` (Django Channels, and the SQL group-by-label-name join)

## Documents and process — §5

- [x] `docs/plan.md` committed before any code — commit `0e781ffbf`, before the backend commit `22d00f798`
- [x] `docs/objectives.md` states CPU, RAM, operating system and the cloned CVAT commit SHA — commit `d388d8ed7`; machine table includes CPU, RAM, OS and SHA `d14126f5...`
- [x] This file exists, written before the work started — commit `45e611123`, before any code
- [x] Commits are incremental, not one large commit at the end — 12 feature commits, each a single step (list in PR)
- [x] Commit messages say what changed and why — each message describes the change and, where relevant, the reason (e.g. `d45548c8d`, `4a36bc145`)
- [x] Everything I did not finish is listed in the section below

## Submission — §10

- [x] Branch `dev-test01` pushed to my own fork
- [x] One pull request, `dev-test01` → `develop` of my fork, and not against `cvat-ai/cvat`
- [ ] Loom recording, 5 minutes or less — recording still to be produced
- [ ] Pull request link and Loom link sent — Loom pending

## Not finished

- The WebSocket end-to-end script (`%TEMP%\pwcheck\ws-e2e.js`) that drives the page
  through login → live update → forced server restart → reconnect was built but the
  restart leg was not re-run after the final server fix; the handshake/auth-close-code
  checks and the reconnect loop itself were verified. Declared here rather than hidden.
- Any runtime integration check of the last docs-only commits (they contain no code).