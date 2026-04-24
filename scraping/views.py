import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from scraping.models import JobListing


def _serialize_job(job):
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "location": job.location,
        "link": job.link,
        "date_scraped": job.date_scraped.isoformat() if job.date_scraped else None,
        "is_relevant": job.is_relevant,
        "relevance_score": job.relevance_score,
        "extracted_skills": job.extracted_skills or [],
        "nlp_processed": job.nlp_processed,
        "is_relevant_human_label": job.is_relevant_human_label,
    }


@require_GET
def job_list(request):
    """List all jobs with optional filtering."""
    queryset = JobListing.objects.all().order_by("-date_scraped")

    search = request.GET.get("search")
    if search:
        queryset = queryset.filter(title__icontains=search)

    skill = request.GET.get("skill")
    if skill:
        queryset = queryset.filter(extracted_skills__contains=skill)

    relevant = request.GET.get("relevant")
    if relevant is not None:
        queryset = queryset.filter(is_relevant=(relevant.lower() == "true"))

    jobs = list(queryset[:100])
    return JsonResponse([_serialize_job(j) for j in jobs], safe=False)


@require_GET
def job_detail(request, pk):
    try:
        job = JobListing.objects.get(pk=pk)
    except JobListing.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)
    return JsonResponse(_serialize_job(job))


@csrf_exempt
@require_POST
def job_label(request, pk):
    try:
        job = JobListing.objects.get(pk=pk)
    except JobListing.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)

    body = json.loads(request.body.decode("utf-8"))
    is_relevant = body.get("is_relevant")
    if is_relevant is not None:
        job.is_relevant_human_label = bool(is_relevant)
        job.save(update_fields=["is_relevant_human_label"])
    return JsonResponse({"success": True})


@require_GET
def unlabeled_jobs(request):
    """Return jobs without human labels, limited to 50."""
    queryset = JobListing.objects.filter(is_relevant_human_label__isnull=True).order_by("?")[:50]
    return JsonResponse([_serialize_job(j) for j in queryset], safe=False)
