from django.contrib import admin
from .models import JobListing

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'date_scraped')
    search_fields = ('title', 'company', 'location')
    list_filter = ('company', 'date_scraped')
    ordering = ('-date_scraped',)
