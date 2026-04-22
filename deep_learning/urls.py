"""URL routes for ML API endpoints."""

from django.urls import path

from deep_learning import views

urlpatterns = [
    path("classify/", views.classify_job, name="ml-classify"),
    path("stats/", views.ml_stats, name="ml-stats"),
    path("process-batch/", views.process_batch, name="ml-process-batch"),
    path("health/", views.ml_health, name="ml-health"),
]
