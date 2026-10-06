# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from cvat.apps.engine.permissions import TaskPermission
from cvat.apps.engine.types import ExtendedRequest

if TYPE_CHECKING:
    from rest_framework.viewsets import ViewSet

    from cvat.apps.engine.models import Task


class TaskAnnotationStatsPermission(TaskPermission):
    """Reuses CVAT's task permission rules to protect the statistics endpoint."""

    @classmethod
    def _get_scopes(
        cls, request: ExtendedRequest, view: ViewSet, obj: Task | None
    ) -> list["TaskAnnotationStatsPermission.Scopes"]:
        return [cls.Scopes.VIEW]
