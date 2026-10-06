# SPDX-License-Identifier: MIT

from django.urls import path

from . import views

urlpatterns = [
    path(
        "tasks/<int:pk>/annotation-stats",
        views.AnnotationStatsViewSet.as_view({"get": "retrieve"}, detail=True),
        name="annotation-stats",
    ),
]
