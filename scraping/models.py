from django.db import models

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

    def __str__(self):
        return f"{self.title} at {self.company}"