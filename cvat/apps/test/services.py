# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections import Counter

from django.db.models import Count, QuerySet

from cvat.apps.engine.models import (
    JobType,
    Label,
    LabeledImage,
    LabeledShape,
    LabeledTrack,
    Task,
)

# Grouping keys accepted by the endpoint, mapped to the annotation fields they
# are aggregated by. The extra grouping key requested for the follow-up
# ("source") will be added here together with its test.
GROUP_FIELDS = {
    "label": "label_id",
}

# Only regular annotation jobs hold annotations that should be counted.
# Ground-truth and consensus jobs are excluded.
_ENGINE_JOB_FILTER = {"job__type": JobType.ANNOTATION.value}

# Shape and track rows can be nested (labelless parents of skeletons and
# sub-tracks); only the top-level rows represent a real annotation.
_NESTED_ANNOTATION_MODELS = (LabeledShape, LabeledTrack)
# Image annotations cannot nest, so their table has no parent column.
_FLAT_ANNOTATION_MODELS = (LabeledImage,)


def _count_grouped_by(queryset: QuerySet, field: str) -> Counter:
    grouped = queryset.values(field).annotate(count=Count("id"))
    return Counter(dict(grouped.values_list(field, "count")))


def get_annotation_counts(task: Task, group_by: str = "label") -> Counter:
    """Return {group value: count} for every annotation of a task.

    Aggregation happens in the database: on the validation task this reduces
    41,866 rows to 80 label ids before any of them reaches the Python process.

    Labels are grouped by primary key and the display names are resolved in one
    extra lookup, not in the same SQL statement. Joining for the name in the
    statement gives the planner a chance to miscalculate the number of shapes
    per label and choose a scan of the whole annotation table once per label
    (measured at ~3 s on the validation task; see docs/perf/annotation-stats.md).
    Grouping by a primary key keeps the plan a single scan plus a small sort.
    """
    if group_by not in GROUP_FIELDS:
        raise ValueError(f"Unsupported group_by value: {group_by!r}")

    field = GROUP_FIELDS[group_by]
    task_filter = {"job__segment__task_id": task.id, **_ENGINE_JOB_FILTER}

    counts: Counter = Counter()
    for model in _NESTED_ANNOTATION_MODELS:
        queryset = model.objects.filter(**task_filter, parent__isnull=True)
        counts.update(_count_grouped_by(queryset, field))

    for model in _FLAT_ANNOTATION_MODELS:
        queryset = model.objects.filter(**task_filter)
        counts.update(_count_grouped_by(queryset, field))

    if group_by == "label":
        names = dict(Label.objects.filter(id__in=counts).values_list("id", "name"))
        counts = Counter(
            {names.get(label_id, f"label {label_id}"): count for label_id, count in counts.items()}
        )

    return counts
