from django.contrib import admin
from .models import JobListing

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'is_relevant', 'nlp_processed', 'date_scraped')
    search_fields = ('title', 'company', 'location')
    list_filter = ('nlp_processed', 'is_relevant', 'company', 'date_scraped')
    ordering = ('-date_scraped',)
