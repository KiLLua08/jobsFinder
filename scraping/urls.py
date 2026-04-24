from django.urls import path
from scraping import views

urlpatterns = [
    path("jobs/", views.job_list, name="job-list"),
    path("jobs/unlabeled/", views.unlabeled_jobs, name="unlabeled-jobs"),
    path("jobs/<int:pk>/", views.job_detail, name="job-detail"),
    path("jobs/<int:pk>/label/", views.job_label, name="job-label"),
]
