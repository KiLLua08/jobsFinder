from django.db import models
from django.conf import settings

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