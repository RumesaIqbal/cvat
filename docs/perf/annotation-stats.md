# Measured performance: MO-1

Raw measurement recorded for MO-1 (see `docs/objectives.md`). Measured on
the machine described there; the numbers are not a reference machine.

- **Date**: 6 October 2026.
- **Measured build**: commit `d45548c8d`.
- **Endpoint**: `GET /api/tasks/1/annotation-stats?group_by=label` over plain
  HTTP on `localhost:8080`, admin via HTTP basic auth, full JSON body received.

## Conditions

- Task 1: COCO 2017 validation set, 41,866 shapes, 80 labels.
- Nothing else running on the machine. The eight RQ worker containers
  (`import`, `export`, `annotation`, `chunks`, `utils`, `webhooks`,
  `consensus`, `quality_reports`) were stopped before measuring: in this
  environment they idle-spin at roughly 80–100% CPU per container even with an
  empty queue, which drags every wall-clock number up and does not represent
  the machine described in `docs/objectives.md`.
- One warm-up request was sent and discarded, then five timed runs, each on a
  fresh connection, same shell session (`scripts/measure-annotation-stats.ps1`).

## Raw runs

```
URL: http://localhost:8080/api/tasks/1/annotation-stats?group_by=label
Warm-up request (discarded):
  588 ms  (status 200, total 41866)
run 1: 575 ms  (status 200, total 41866)
run 2: 444 ms  (status 200, total 41866)
run 3: 429 ms  (status 200, total 41866)
run 4: 606 ms  (status 200, total 41866)
run 5: 440 ms  (status 200, total 41866)
```

## Result

| Metric | Value |
|---|---|
| Median of 5 runs | **444 ms** |
| Min | 429 ms |
| Max | **606 ms** |
| Spread (max − min) | 177 ms |

**MO-1 met.** Target was median ≤ 500 ms and no single run above 1,000 ms;
measured median 444 ms, max 606 ms.

## What made the target reachable

The first version of the endpoint grouped by `label__name` in the same SQL
statement. PostgreSQL's row estimates for the number of shapes per label were
badly off (statistics stale right after a bulk import), so it chose a plan that
scanned the whole `engine_labeledshape` table once per label — 80 scans of
41,866 rows, ~3.3M join-filter rejections, ~3.0 s in the database alone.
Through the full stack the endpoint measured around 2.5–3.5 s.

The counting query now groups by `label_id` (a primary key, so the planner
keeps a single scan + small sort, ~0.23 s in the database) and display names
are resolved afterwards with one lookup by id. The five runs above include the
full stack: traefik → nginx → uvicorn → Django → PostgreSQL.

A caveat seen while measuring: the first handful of requests after the server
container restarts run slower (~1.1 s median) while the interpreter and
database buffers warm up. `docs/objectives.md` explicitly excludes cold-start
behaviour after a rebuild from this objective, and the numbers above are the
steady state.