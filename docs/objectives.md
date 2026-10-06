# Objectives

Targets set before the measurement was taken, in the format required by §6.
The numbers below are the machine I ran on, not a reference machine.

## Machine

| Field | Value |
|---|---|
| CPU | 11th Gen Intel(R) Core(TM) i7-1185G7 @ 3.00GHz, 4 cores / 8 logical processors |
| RAM | 31.7 GB total |
| Operating system | Microsoft Windows 11 Pro, version 10.0.26300 (build 26300) |
| CVAT commit cloned | `d14126f522d0b6149797ea1bf067928cfc4d5795` |
| Container runtime | Docker 29.6.2 with Compose v5.3.1, WSL2 backend |
| Sample data | COCO 2017 validation set: 5,000 images, 41,866 shapes over 80 labels, task id 1 |

## MO-1 — Endpoint response time

| Field | Value |
|---|---|
| **ID** | MO-1 |
| **What is measured** | Wall-clock time for one complete request of `GET /api/tasks/1/annotation-stats?group_by=label`, from leaving the client to the full JSON response being received, over plain HTTP on `localhost:8080`. |
| **How** | `scripts/measure-annotation-stats.ps1` wraps the request in a .NET `Stopwatch` and prints each run. One warm-up run is discarded so the first request is not paying for connection setup and Django's import cache. The five timed runs each open a fresh connection, so connection setup is inside every reported number. Raw output is pasted into `docs/perf/annotation-stats.md`. |
| **Target** | Median of 5 runs at or below **500 ms**, with no single run above 1,000 ms. |
| **Conditions** | Local Docker stack on the machine described above, task 1 with 41,866 shapes, admin session via HTTP basic auth, nothing else running on the machine, same shell session as the warm-up. |
| **Not included** | Cold-start behaviour after `docker compose up`, the first request after any image rebuild, other tasks, and browser rendering time — the graph drawing is a separate thing from the endpoint answering. |

**Why 500 ms.** The page re-reads this endpoint when annotations change, so the number
is what a person waits on repeatedly, not once. 500 ms is roughly the point at which a
wait stops feeling like an action and starts feeling like a delay, and it is tight enough
that a naive implementation — reading every shape row and grouping them in Python rather
than in the database — is expected to miss it. A target I clear without changing how the
query is written would not be worth reporting.

**How it will be judged.** Reported as median **and** spread (`max − min`), with all five
raw runs visible. One number on its own is not a measurement (§6).
