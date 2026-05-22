from django.urls import path
from scraping import views

urlpatterns = [
    path("jobs/", views.job_list, name="job-list"),
    path("jobs/unlabeled/", views.unlabeled_jobs, name="unlabeled-jobs"),
    path("jobs/<int:pk>/", views.job_detail, name="job-detail"),
    path("jobs/<int:pk>/label/", views.job_label, name="job-label"),
    # scrape_endpoint handles GET (history) and POST (trigger) on the same path
    path("scrape/", views.scrape_endpoint, name="scrape-endpoint"),
    path("scrape/<int:pk>/status/", views.scrape_status, name="scrape-status"),
]
