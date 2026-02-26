from django.db import models

class JobListing(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    description = models.TextField() # This is for our Deep Learning model later
    location = models.CharField(max_length=255, null=True, blank=True)
    link = models.URLField(unique=True) # unique=True prevents duplicate scrapes
    date_scraped = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"