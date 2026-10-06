# SPDX-License-Identifier: MIT

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from cvat.apps.engine.models import Task

from . import services
from .permissions import TaskAnnotationStatsPermission


class AnnotationStatsViewSet(viewsets.GenericViewSet):
    """Counts the annotations of a single task, grouped by the requested key."""

    iam_permission_class = TaskAnnotationStatsPermission
    queryset = Task.objects
    filter_backends: tuple = ()

    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        group_by = request.query_params.get("group_by", "label")

        try:
            counts = services.get_annotation_counts(task, group_by)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        ordered = sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))
        return Response(
            {
                "task": task.id,
                "group_by": group_by,
                "total": sum(counts.values()),
                "counts": [{"key": key, "count": value} for key, value in ordered],
            }
        )
