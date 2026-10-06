# SPDX-License-Identifier: MIT

"""Pure-ASGI WebSocket endpoint for live annotation statistics.

Uvicorn does not run Django's HTTP middleware for websocket scopes, so this
handler does the three things the REST endpoint's stack would have done, each
in a worker thread because the underlying libraries (Django ORM, the OPA
client) are synchronous:

1. resolve the user from the same `sessionid` cookie the web UI logs in with;
2. ask the exact same OPA rule as the REST endpoint whether that user may view
   the task (`TaskAnnotationStatsPermission`, which is `TaskPermission` with a
   single VIEW scope);
3. re-run the counting query on a fixed interval and push the JSON result only
   when it changed.

The first push happens on connect, so a freshly connected page always receives
a full snapshot without having to re-fetch the REST endpoint.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any
from urllib.parse import parse_qs

from django.contrib.sessions.backends.db import SessionStore

from cvat.apps.engine.models import Task
from cvat.apps.iam.models import User

from .permissions import TaskAnnotationStatsPermission
from .services import get_annotation_counts

_ROUTE = re.compile(r"^/api/tasks/(?P<task_id>\d+)/annotation-stats/ws$")
_GROUP_BY_DEFAULT = "label"
_POLL_INTERVAL_SECONDS = 1

logger = logging.getLogger(__name__)


def _parse_cookies(scope: dict[str, Any]) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for name, value in scope.get("headers", []):
        if name != b"cookie":
            continue
        for part in value.decode().split(";"):
            if "=" in part:
                cookie_name, cookie_value = part.strip().split("=", 1)
                cookies[cookie_name] = cookie_value
    return cookies


def _resolve_user(session_key: str) -> User | None:
    if not session_key:
        return None

    session = SessionStore(session_key=session_key).load()
    user_id = session.get("_auth_user_id")
    if not user_id:
        return None

    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def _privilege(user: User) -> str | None:
    from django.conf import settings

    priorities = {role: priority for priority, role in enumerate(settings.IAM_ROLES)}
    groups = sorted(
        user.groups.filter(name__in=priorities),
        key=lambda group: priorities[group.name],
    )
    return groups[0].name if groups else None


def _can_view_counts(user: User, task_id: int) -> bool:
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return False

    permission = TaskAnnotationStatsPermission(
        scope=TaskAnnotationStatsPermission.Scopes.VIEW,
        obj=task,
        user_id=user.id,
        group_name=_privilege(user),
        org_specified=False,
        org_id=None,
        org_owner_id=None,
        org_role=None,
    )
    return permission.check_access().allow


def _counts_json(task_id: int, group_by: str) -> str:
    task = Task.objects.get(id=task_id)
    counts = get_annotation_counts(task, group_by)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))
    payload = {
        "task": task.id,
        "group_by": group_by,
        "total": sum(counts.values()),
        "counts": [{"key": key, "count": value} for key, value in ordered],
    }
    return json.dumps(payload)


async def _serve_websocket(scope: dict[str, Any], send) -> None:
    async def reject(code: int) -> None:
        # Accept before closing so the client receives the code instead of a
        # plain HTTP-level rejection (uvicorn turns a close-before-accept
        # into a 403, which browsers report as an abnormal disconnection).
        await send({"type": "websocket.accept"})
        await send({"type": "websocket.close", "code": code})

    match = _ROUTE.match(scope["path"])
    if not match:
        await reject(4404)
        return

    task_id = int(match.group("task_id"))
    query = parse_qs((scope.get("query_string") or b"").decode())
    group_by = (query.get("group_by") or [_GROUP_BY_DEFAULT])[0]
    if group_by not in {"label", "source"}:
        await reject(4400)
        return

    cookies = _parse_cookies(scope)
    user = await asyncio.to_thread(_resolve_user, cookies.get("sessionid", ""))
    if user is None:
        await reject(4401)
        return

    allowed = await asyncio.to_thread(_can_view_counts, user, task_id)
    if not allowed:
        await reject(4403)
        return

    await send({"type": "websocket.accept"})

    last_payload: str | None = None
    while True:
        try:
            payload = await asyncio.to_thread(_counts_json, task_id, group_by)
        except Exception:  # noqa: BLE001 - a failed recompute must not kill the socket
            logger.warning("annotation stats recompute failed for task %s", task_id, exc_info=True)
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)
            continue

        if payload != last_payload:
            await send({"type": "websocket.send", "text": payload})
            last_payload = payload

        await asyncio.sleep(_POLL_INTERVAL_SECONDS)


async def handle_websocket(scope: dict[str, Any], receive, send) -> None:
    try:
        await _serve_websocket(scope, send)
    except Exception:  # noqa: BLE001 - a dropped client must not crash the worker
        logger.debug("annotation stats websocket closed", exc_info=True)
