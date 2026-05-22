from django.db import models
from django.conf import settings


class ScrapeJob(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    query = models.CharField(max_length=255)
    site = models.CharField(max_length=20)
    pages = models.IntegerField()
    jobs_found = models.IntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ScrapeJob #{self.pk} [{self.status}] {self.query} on {self.site}"


class JobListing(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    description = models.TextField() # This is for our Deep Learning model later
    location = models.CharField(max_length=255, null=True, blank=True)
    link = models.URLField(max_length=1000, unique=True) # unique=True prevents duplicate scrapes
    date_scraped = models.DateTimeField(auto_now_add=True)
    
    # NLP / Deep Learning Fields
    is_relevant = models.BooleanField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    nlp_processed = models.BooleanField(default=False)
    
    # Human Labeling for ML Fine-tuning
    is_relevant_human_label = models.BooleanField(null=True, blank=True)
    labeled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"