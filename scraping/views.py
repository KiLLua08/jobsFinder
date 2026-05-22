import json
import logging
import threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from scraping.models import JobListing, ScrapeJob

logger = logging.getLogger(__name__)

PAGE_SIZE = 20


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


def _serialize_scrape_job(scrape_job):
    """Serialize a ScrapeJob to a dict for API responses.

    jobs_found is returned as null when status is pending or running,
    regardless of the stored value (requirement 2.5).
    """
    in_progress = scrape_job.status in (ScrapeJob.STATUS_PENDING, ScrapeJob.STATUS_RUNNING)
    return {
        "id": scrape_job.id,
        "status": scrape_job.status,
        "query": scrape_job.query,
        "site": scrape_job.site,
        "pages": scrape_job.pages,
        "jobs_found": None if in_progress else scrape_job.jobs_found,
        "started_at": scrape_job.started_at.isoformat() if scrape_job.started_at else None,
        "finished_at": scrape_job.finished_at.isoformat() if scrape_job.finished_at else None,
        "error_message": scrape_job.error_message,
        "created_at": scrape_job.created_at.isoformat() if scrape_job.created_at else None,
    }


@require_GET
def job_list(request):
    """List jobs with optional filtering and cursor pagination."""
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

    try:
        page = max(1, int(request.GET.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    total = queryset.count()
    offset = (page - 1) * PAGE_SIZE
    jobs = list(queryset[offset: offset + PAGE_SIZE])

    return JsonResponse({
        "results": [_serialize_job(j) for j in jobs],
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "total_pages": max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
    })


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
        update_fields = ["is_relevant_human_label"]
        job.is_relevant_human_label = bool(is_relevant)
        # Populate labeled_by if the request comes from an authenticated user.
        if request.user.is_authenticated:
            job.labeled_by = request.user
            update_fields.append("labeled_by")
        job.save(update_fields=update_fields)
    return JsonResponse({"success": True})


@require_GET
def unlabeled_jobs(request):
    """Return jobs without human labels, limited to 50."""
    queryset = JobListing.objects.filter(is_relevant_human_label__isnull=True).order_by("?")[:50]
    return JsonResponse([_serialize_job(j) for j in queryset], safe=False)


@csrf_exempt
def scrape_endpoint(request):
    """Dispatch GET → scrape_history, POST → scrape_trigger."""
    if request.method == "GET":
        return scrape_history(request)
    if request.method == "POST":
        return scrape_trigger(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def scrape_history(request):
    """Return the 20 most recent ScrapeJob records ordered by created_at desc."""
    jobs = ScrapeJob.objects.order_by("-created_at")[:20]
    return JsonResponse([_serialize_scrape_job(j) for j in jobs], safe=False)


def scrape_trigger(request):
    """Start a scrape job: create a ScrapeJob record, then run in a background thread."""
    body = json.loads(request.body.decode("utf-8")) if request.body else {}
    query = str(body.get("query", "Software Engineer")).strip() or "Software Engineer"
    site = str(body.get("site", "linkedin")).strip().lower()
    pages = int(body.get("pages", 3))
    enrich = bool(body.get("enrich", True))  # default True; set False for fast mode

    if site not in ("linkedin", "indeed", "all"):
        return JsonResponse({"error": "site must be linkedin, indeed, or all"}, status=400)

    # Concurrent scrape guard: only block on running (not pending) jobs.
    running_job = ScrapeJob.objects.filter(status=ScrapeJob.STATUS_RUNNING).first()
    if running_job:
        return JsonResponse(
            {
                "error": "A scrape is already running",
                "job_id": running_job.id,
            },
            status=409,
        )

    scrape_job = ScrapeJob.objects.create(
        status=ScrapeJob.STATUS_PENDING,
        query=query,
        site=site,
        pages=pages,
    )

    def _run(job_id):
        from scraping.scrapers import LinkedInScraper, IndeedScraper
        from scraping.utils.db import save_jobs_to_db

        try:
            job = ScrapeJob.objects.get(pk=job_id)
            job.status = ScrapeJob.STATUS_RUNNING
            job.started_at = timezone.now()
            job.save(update_fields=["status", "started_at"])

            scrapers = (
                [LinkedInScraper, IndeedScraper] if site == "all"
                else [LinkedInScraper if site == "linkedin" else IndeedScraper]
            )
            total_saved = 0
            for cls in scrapers:
                scraped_jobs = cls(max_pages=pages, enrich=enrich).run(query)
                if scraped_jobs:
                    created, _ = save_jobs_to_db(scraped_jobs)
                    total_saved += created

            job.status = ScrapeJob.STATUS_COMPLETED
            job.finished_at = timezone.now()
            job.jobs_found = total_saved
            job.save(update_fields=["status", "finished_at", "jobs_found"])

        except Exception as exc:
            logger.error("Scrape thread error for job %s: %s", job_id, exc, exc_info=True)
            try:
                ScrapeJob.objects.filter(pk=job_id).update(
                    status=ScrapeJob.STATUS_FAILED,
                    finished_at=timezone.now(),
                    error_message=str(exc),
                )
            except Exception:
                logger.exception("Failed to update ScrapeJob %s to failed state", job_id)

    thread = threading.Thread(target=_run, args=(scrape_job.id,), daemon=True)
    thread.start()

    return JsonResponse(_serialize_scrape_job(scrape_job), status=200)


@require_GET
def scrape_status(request, pk):
    """Return the current state of a ScrapeJob by id."""
    try:
        scrape_job = ScrapeJob.objects.get(pk=pk)
    except ScrapeJob.DoesNotExist:
        return JsonResponse({"error": "Scrape job not found"}, status=404)
    return JsonResponse(_serialize_scrape_job(scrape_job))
