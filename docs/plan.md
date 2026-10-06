# Plan — Annotation Analytics (CVAT)

Branch `dev-test01`, fork `RumesaIqbal/cvat`, base commit `d14126f522d0b6149797ea1bf067928cfc4d5795`.
Written before any code, as required by §5.3. Times are of my own work; Docker pulls, image
builds and the dataset import are excluded per §2.

## Order of work

| # | Step | Depends on | Budget |
|---|------|-----------|--------|
| 0 | Fork, clone, stack up, superuser, COCO val2017 (5,000 images) imported | — | 0:45 (mostly waiting) |
| 1 | `docs/plan.md` committed alone, before any code | 0 | 0:15 |
| 2 | Counting API in a new Django app `test` | 1 | 1:00 |
| 3 | Page + graph + empty state + failed request | 2 | 1:30 |
| 4 | Auth proof: 401 with no login, 403 without task access | 2 | 0:45 |
| 5 | Speed target, measured 5 runs, raw output saved | 2,3 | 1:00 |
| 6 | One extra filter/grouping + written rationale | 3 | 0:30 |
| 7 | WebSocket live updates + reconnect recovery | 3,4 | 1:15 |
| 8 | `docs/objectives.md`, `docs/definition-of-done.md`, evidence | 5,6 | 0:45 |
| 9 | Loom (≤5 min) + PR `dev-test01` → `develop` of my fork | 8 | 0:45 |

Steps 1–3 are the floor (items 1–4 of §3) and are not traded against anything.
Step 7 is only started once item 4 works, per §3.

## What I will build

**Endpoint (step 2).** `GET /api/tasks/{task_id}/annotation-stats?group_by=label|source`,
returning `{"task_id", "group_by", "total", "counts": [{"key", "count"}]}` sorted count-desc.
Backend lives entirely in a new app `cvat/apps/test` — `services.py` holds the counting query,
`views.py` a `GenericViewSet` with `retrieve()`, `urls.py` the route, `permissions.py` a
subclass of `TaskPermission`. Four one-line hooks into core: `INSTALLED_APPS`, `urls.py`
include, an ASGI wrapper, and `proxy_http_version 1.1` in nginx for the WebSocket handshake.
No models, so no migrations.

**Page (step 3).** A standalone React route `/tasks/:id/annotation-stats` registered in
`cvat-app.tsx`, built from components in `cvat-ui/src/components/annotation-stats-page/`.
`chart.js` and `react-chartjs-2` are already dependencies. Three states: counts, empty
(no annotations yet), error (request failed — message + retry). Nothing is added to the
task actions menu (see skips).

**Auth (step 4).** No custom auth code. CVAT's `TokenAuthentication` is the first default
authenticator, so an anonymous request carries no `WWW-Authenticate` gap and resolves to
401; the route is declared `detail=True`, so `PolicyEnforcer` defers to object permission
and OPA answers 403 when the user lacks access to that task. Proven with three curl calls.

**Speed (step 5).** Target set in `docs/objectives.md` before measuring; measured
client-side through traefik with a PowerShell timer, 1 warm-up + 5 timed runs, raw output
plus median and max−min spread pasted into `docs/perf/annotation-stats.md`.

**Extra filter (step 6).** `group_by=source`, splitting imported (`file`/`cvat`/`ground_truth`)
from hand-drawn annotations. Rationale written alongside it: on an imported COCO task it is the
split a reviewer actually asks for, and it is free — same three queries, different grouping key.

**Live updates (step 7).** A pure-ASGI WebSocket endpoint on
`/api/tasks/{id}/annotation-stats/ws`: cookie-Session auth and `TaskPermission.check_access()`
run in a thread, then the same counting function is re-evaluated every second and pushed only
when the result changed. The client reconnects with capped exponential backoff and takes a full
snapshot on every successful connect, which is what makes recovery work without a page reload.

## What I have already decided to skip

- **No entry in the task actions menu** — the UI is reachable by URL. Adding it means touching
  a shared component every other page depends on; the risk is not worth it and §3 only asks
  for "a page in the web interface".
- **No cross-worker broadcast** (no Redis pub/sub, no Channels). With `NUMPROCS=2` each uvicorn
  process owns its own connections and recomputes, so no coordination is needed for correctness.
- **No caching layer** — the query is measured first; if it clears the target without one,
  a cache would only add an invalidation problem.
- **No OpenAPI schema entry**, no `generateschema`.
- **No video/frame-aware counting**, no multi-organisation demonstration, no label-colour or
  annotation-size breakdowns.

## Decision record (item 10)

**Taken: a plain ASGI WebSocket handler inside `cvat/apps/test/asgi.py`, zero new
dependencies.** It short-circuits `scope["type"] == "websocket"` before Django is invoked and
reuses CVAT's own `TaskPermission.check_access()` for authorisation.

**Rejected: Django Channels + `channels-redis`.** It is the idiomatic answer and would give me
pub/sub and channel layers for free.

**What rejecting it cost:** roughly 45 minutes of hand-written code — token parsing, a heartbeat,
backoff on the client — that Channels would have given me, and no fan-out to other workers.
I would have to write the auth handshake myself rather than taking middleware off the shelf.

**Why I still rejected it:** CVAT's runtime image has pip deleted, so adding packages means
editing every `requirements/*.txt` and rebuilding the whole server image — against a clock, with
a known-flaky network. It also drags in an ASGI routing layer over an existing `urls.py` I would
be editing anyway. The hand-rolled version is ~80 lines, has no new supply chain, and keeps the
change contained in one app.

## Plan changes as they happen

Any step that lands differently from the table above gets a note here saying why, rather than
being quietly rewritten at the end.
