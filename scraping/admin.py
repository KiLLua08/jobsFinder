from django.contrib import admin
from .models import JobListing, ScrapeJob


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'is_relevant', 'nlp_processed', 'date_scraped')
    search_fields = ('title', 'company', 'location')
    list_filter = ('nlp_processed', 'is_relevant', 'company', 'date_scraped')
    ordering = ('-date_scraped',)


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'query', 'site', 'status', 'jobs_found', 'created_at', 'finished_at')
    list_filter = ('status', 'site')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'started_at', 'finished_at')
