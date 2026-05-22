# JobsFinder

A full-stack AI-powered job aggregation platform. JobsFinder scrapes job listings from LinkedIn and Indeed, runs them through a deep learning pipeline to classify relevance and extract technical skills, lets users label jobs manually to build a training dataset, and supports fine-tuning a custom classifier on those labels.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Data Models](#data-models)
- [Scraping Architecture](#scraping-architecture)
- [ML Pipeline](#ml-pipeline)
- [Fine-tuning Pipeline](#fine-tuning-pipeline)
- [REST API Reference](#rest-api-reference)
- [Frontend Pages](#frontend-pages)
- [Scrape Job Progress](#scrape-job-progress)
- [Management Commands](#management-commands)
- [Running the Project](#running-the-project)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Design Decisions](#design-decisions)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0 / Python 3.12 |
| Frontend | Next.js 14 (App Router, TypeScript) |
| Database | PostgreSQL 15 (SQLite for local dev) |
| Scraping | Selenium + BeautifulSoup4 |
| ML / NLP | HuggingFace Transformers + PyTorch |
| Containers | Docker Compose (6 services) |
| Package manager | uv (Python), npm (Node) |
| Testing | Django TestCase + Hypothesis (property-based) |
| CI/CD | GitHub Actions |

---

## Architecture

Six Docker Compose services:

| Service | Description | Port(s) |
|---|---|---|
| **web** | Django REST API | 8000 |
| **frontend** | Next.js app | 3000 |
| **db** | PostgreSQL 15 | 5432 |
| **chrome** | Selenium standalone Chrome | 4444 (VNC: 7900) |
| **ml-worker** | Idle Django container for ML commands (2 GB shm, HuggingFace cache mounted) | — |
| **pgadmin4** | pgAdmin web UI | 5050 |

The frontend proxies all `/api/*` requests to the Django backend via Next.js rewrites configured in `next.config.ts`, using the `NEXT_PUBLIC_API_URL` environment variable. As a result, `API_BASE = ""` in `api.ts` is intentional — Next.js handles the routing transparently.

---

## Project Structure

```
jobsFinder/
├── backend/                    # Django project config
│   ├── settings.py             # DB, installed apps, middleware
│   ├── urls.py                 # Root URL routing
│   ├── wsgi.py / asgi.py
├── scraping/                   # Scraping Django app
│   ├── models.py               # JobListing, ScrapeJob models
│   ├── views.py                # REST API views
│   ├── urls.py                 # API routes
│   ├── admin.py                # Django admin registrations
│   ├── middleware.py           # Custom CORS middleware
│   ├── scrapers/
│   │   ├── base.py             # BaseScraper (Template Method pattern)
│   │   ├── linkedin.py         # LinkedInScraper
│   │   ├── indeed.py           # IndeedScraper
│   ├── utils/
│   │   ├── anti_detection.py   # Random User-Agent, random delays
│   │   ├── db.py               # save_jobs_to_db() helper
│   ├── management/commands/
│   │   ├── scrape.py           # python manage.py scrape
├── deep_learning/              # ML Django app
│   ├── pipeline.py             # ModelCache, RelevanceClassifier, SkillsExtractor, BatchProcessor
│   ├── models.py               # MLModelMetadata, InferenceLog
│   ├── views.py                # ML REST API endpoints
│   ├── urls.py                 # ML API routes
│   ├── apps.py                 # AppConfig with startup model warmup
│   ├── signals.py              # post_save signal for auto ML processing
│   ├── admin.py                # Admin for MLModelMetadata, InferenceLog
│   ├── training/
│   │   ├── train.py            # run_training() fine-tuning loop
│   │   ├── job_dataset.py      # PyTorch Dataset from JSONL
│   │   ├── metrics.py          # accuracy, precision, recall, F1
│   ├── management/commands/
│   │   ├── analyze_jobs.py     # Batch ML processing via CLI
│   │   ├── export_training_data.py  # Export labeled jobs to JSONL
│   │   ├── train_classifier.py # Fine-tune + save MLModelMetadata
├── frontend/                   # Next.js 14 app
│   ├── app/
│   │   ├── page.tsx            # Home page (live stats + feature cards)
│   │   ├── jobs/page.tsx       # Job listings with search/filter/pagination
│   │   ├── jobs/[id]/page.tsx  # Job detail with ML analysis + labeling
│   │   ├── scrape/page.tsx     # Scrape trigger + real-time progress + history
│   │   ├── dashboard/page.tsx  # ML stats, model status, batch processing
│   │   ├── classify/page.tsx   # Interactive ML classify demo
│   │   ├── label/page.tsx      # Human labeling queue (keyboard shortcuts)
│   │   ├── lib/api.ts          # Typed API client
│   │   ├── lib/types.ts        # TypeScript interfaces
│   ├── components/ui/          # shadcn/ui components
│   ├── next.config.ts          # API proxy rewrites
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml              # Python deps (uv)
├── uv.lock
├── manage.py
```

---

## Data Models

### `JobListing` (scraping app)

| Field | Type | Description |
|---|---|---|
| `title` | CharField | Job title |
| `company` | CharField | Company name |
| `description` | TextField | Full job description |
| `location` | CharField | Location (nullable) |
| `link` | URLField (unique) | Original job URL — prevents duplicates |
| `date_scraped` | DateTimeField | Auto-set on creation |
| `is_relevant` | BooleanField | ML classification result (`null` = unprocessed) |
| `relevance_score` | FloatField | Confidence score 0.0–1.0 |
| `extracted_skills` | JSONField | List of detected tech skills |
| `nlp_processed` | BooleanField | Whether ML pipeline has run |
| `is_relevant_human_label` | BooleanField | Ground truth label set by human |
| `labeled_by` | FK → User | Who labeled it |

### `ScrapeJob` (scraping app)

Tracks each scrape run lifecycle.

| Field | Type | Description |
|---|---|---|
| `status` | CharField | `pending` / `running` / `completed` / `failed` |
| `query` | CharField | Search query used |
| `site` | CharField | `linkedin` / `indeed` / `all` |
| `pages` | IntegerField | Pages requested |
| `jobs_found` | IntegerField | New jobs saved (null until completed) |
| `started_at` | DateTimeField | When thread started |
| `finished_at` | DateTimeField | When thread finished |
| `error_message` | TextField | Exception message if failed |
| `created_at` | DateTimeField | Auto-set |

### `MLModelMetadata` (deep_learning app)

Tracks trained model versions.

| Field | Type | Description |
|---|---|---|
| `name` | CharField | Human-readable name |
| `model_type` | CharField | `classifier` / `ner` |
| `version` | CharField | Semantic version e.g. `1.0.0` |
| `huggingface_model_id` | CharField | Base model used |
| `accuracy` | FloatField | Eval accuracy |
| `f1_score` | FloatField | Eval F1 |
| `training_date` | DateTimeField | When trained |
| `is_active` | BooleanField | Whether currently active |

### `InferenceLog` (deep_learning app)

Records every ML inference call for auditing.

| Field | Type | Description |
|---|---|---|
| `job_listing` | FK → JobListing | Which job was processed |
| `model_used` | CharField | Model identifier |
| `model_version` | CharField | Version string |
| `inference_type` | CharField | `classification` / `ner` / `full` |
| `is_relevant` | BooleanField | Result |
| `relevance_score` | FloatField | Confidence |
| `extracted_skills` | JSONField | Skills found |
| `processing_time_ms` | FloatField | Latency |
| `success` | BooleanField | Whether it succeeded |
| `error_message` | TextField | Error if failed |
| `timestamp` | DateTimeField | When it ran |

---

## Scraping Architecture

The scrapers use the **Template Method** design pattern. `BaseScraper` defines the full algorithm skeleton:

1. Start Selenium browser (connects to the Docker Chrome container)
2. Loop pages: fetch URL → parse HTML → collect job cards
3. Enrich jobs (navigate to each job page for full description)
4. Close browser

`LinkedInScraper` and `IndeedScraper` only override `get_search_url()`, `parse_job_cards()`, and `enrich_jobs()`. Adding a new job site requires roughly 50 lines.

### Anti-detection measures

- Pool of 6 real browser User-Agent strings, rotated randomly per session
- Selenium automation flags removed (`excludeSwitches: enable-automation`, `useAutomationExtension: false`)
- Random delays between page loads (2–5 s) and between job description fetches
- LinkedIn description pages fetched with raw `urllib` (not Selenium) — LinkedIn's bot detection is less aggressive against plain HTTP requests
- Indeed description pages use Selenium with a 2–5 s pre-fetch delay and a 3–6 s post-load wait
- Retry with exponential backoff: 3 attempts, waits `2^attempt` seconds between retries

### Deduplication

The `link` field has `unique=True`. `save_jobs_to_db()` uses `update_or_create` on the link — existing jobs are updated, new ones created. Returns `(created, skipped)` counts.

---

## ML Pipeline

### Models used

| Role | Model | Notes |
|---|---|---|
| Classifier | `facebook/bart-large-mnli` | Zero-shot, used by default |
| Classifier (fine-tuned) | `distilroberta-base` | Used if saved at `deep_learning/saved_models/classifier_v1/` |
| NER | `dslim/bert-base-NER` | Token classification for skill extraction |

### ModelCache (Singleton)

Holds loaded HuggingFace pipeline objects in class-level variables. Models are loaded once per process on startup (via `AppConfig.ready()`) and reused for all requests. Startup warmup is skipped for management commands that don't need ML (`migrate`, `test`, etc.) and can be disabled with `ML_SKIP_WARMUP=1`.

### RelevanceClassifier

Runs zero-shot classification with candidate labels: `["relevant job posting", "irrelevant content", "spam"]`. Returns `(is_relevant: bool, score: float)`. Threshold: score ≥ 0.55 = relevant. Input is truncated to 1000 characters.

### SkillsExtractor

Hybrid approach:

1. Regex pattern matching against a hardcoded vocabulary of 35 tech skills (Python, SQL, AWS, Docker, Kubernetes, React, etc.)
2. BERT-NER model run on the same text; any identified tokens that appear in the vocabulary are added

Results are merged into a set, normalized (e.g. `"sql"` → `"SQL"`, `"javascript"` → `"Javascript"`), and returned sorted.

### BatchProcessor

Processes `JobListing` records through both the classifier and extractor. Writes results back to the `JobListing` record and creates an `InferenceLog` entry. Supports a `callback` for progress reporting.

### Auto-processing via Django Signal

A `post_save` signal on `JobListing` automatically runs `BatchProcessor.process_single()` whenever a new job is saved with a description and `nlp_processed=False`. Jobs are classified immediately after scraping with no manual trigger required.

---

## Fine-tuning Pipeline

1. **Label jobs** via the frontend `/label` page or `POST /api/jobs/<id>/label/`
2. **Export labeled data:**
   ```bash
   python manage.py export_training_data
   ```
   Writes `deep_learning/training_data/dataset.jsonl` (JSONL format: `{"text": "...", "label": 0|1}`)
3. **Dry run** — verify data loads correctly:
   ```bash
   python manage.py train_classifier --dry_run
   ```
4. **Train** — fine-tunes `distilroberta-base` with:
   - 85/15 train/val stratified split
   - 3 epochs, batch size 4, gradient accumulation 4 (effective batch 16)
   - fp16 if CUDA is available
   - Best checkpoint loaded at end (metric: F1)
   - Model saved to `deep_learning/saved_models/classifier_v1/`
   - `MLModelMetadata` record created with accuracy, F1, and training date
   - Previous classifier versions deactivated
5. **Pipeline auto-switches** — `ModelCache` checks for the local saved model on load; if it exists, it is used instead of BART

---

## REST API Reference

### Jobs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/jobs/` | List jobs. Params: `search`, `relevant`, `skill`, `page` |
| GET | `/api/jobs/<id>/` | Get single job |
| POST | `/api/jobs/<id>/label/` | Set human label `{"is_relevant": true}` |
| GET | `/api/jobs/unlabeled/` | 50 random unlabeled jobs |

### Scraping

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/scrape/` | Trigger scrape `{"query": "...", "site": "linkedin\|indeed\|all", "pages": 3}`. Returns `ScrapeJob` with `id`. Returns 409 if a scrape is already running. |
| GET | `/api/scrape/` | List 20 most recent `ScrapeJob` records |
| GET | `/api/scrape/<id>/status/` | Poll scrape job status |

### ML

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ml/classify/` | Classify a description `{"description": "..."}` |
| POST | `/api/ml/process-batch/` | Process unprocessed jobs `{"limit": 50}` |
| GET | `/api/ml/stats/` | Total, processed, relevant counts + percentage |
| GET | `/api/ml/health/` | Model load status + active fine-tuned model info |

---

## Frontend Pages

| Page | Route | Description |
|---|---|---|
| Home | `/` | Live stats bar + feature cards linking to all sections |
| Jobs | `/jobs` | Paginated job list with search, relevance filter, skill badges |
| Job Detail | `/jobs/<id>` | Full description, ML analysis card, human labeling buttons |
| Scrape | `/scrape` | Trigger scrape form + real-time progress polling (3 s interval, 10 min timeout) + history table |
| Dashboard | `/dashboard` | ML stats, processing progress bar, model status, batch trigger, fine-tuned model info |
| Classify | `/classify` | Paste any text → instant AI classification + skill extraction demo |
| Label | `/label` | One-at-a-time labeling queue with keyboard shortcuts (Y / N / S) |

---

## Scrape Job Progress

When a scrape is triggered via the frontend:

1. Backend creates a `ScrapeJob` record with `status=pending`, returns its `id`
2. Background thread starts, updates status to `running` with `started_at`
3. Frontend polls `GET /api/scrape/<id>/status/` every 3 seconds
4. Thread completes → `status=completed`, `jobs_found=N`, `finished_at` set
5. Thread fails → `status=failed`, `error_message` set
6. Frontend stops polling on terminal status or after a 10-minute timeout
7. `jobs_found` is masked as `null` in API responses while status is `pending` or `running`
8. Concurrent guard: returns HTTP 409 if a `running` job already exists

---

## Management Commands

```bash
# Scrape jobs
python manage.py scrape --site linkedin --query "Data Scientist" --pages 3
python manage.py scrape --site indeed --query "Python Developer"
python manage.py scrape --site all --query "ML Engineer" --pages 5
python manage.py scrape --site all --query "..." --no-save       # preview only, don't write to DB
python manage.py scrape --site all --query "..." --clear-before  # wipe DB before scraping

# ML pipeline
python manage.py analyze_jobs                    # process all unprocessed jobs
python manage.py analyze_jobs --limit 100        # process up to 100

# Fine-tuning
python manage.py export_training_data                                        # export labeled jobs to JSONL
python manage.py train_classifier --dry_run                                  # verify data loads correctly
python manage.py train_classifier                                             # run full training
python manage.py train_classifier --version 1.2.0                            # specify version
python manage.py train_classifier --model_name distilbert-base-uncased       # use a different base model
```

---

## Running the Project

### Prerequisites

- Docker Desktop
- A `.env` file in the project root:

```env
POSTGRES_PASSWORD=yourpassword
PGADMIN_MAIL=admin@admin.com
PGADMIN_PASSWORD=yourpassword
```

### Docker (recommended)

```bash
docker-compose up --build

# In a second terminal:
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser  # optional
```

Services after startup:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin |
| pgAdmin | http://localhost:5050 |
| Selenium VNC | http://localhost:7900 |

### Local Development (without Docker)

```bash
# Python backend
uv venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
uv pip install -e ".[ml]"
python manage.py migrate
python manage.py runserver

# Next.js frontend (separate terminal)
cd frontend
npm install
npm run dev
```

> Local scraping requires a Selenium server. Run one with:
> ```bash
> docker run -p 4444:4444 selenium/standalone-chrome
> ```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | — | Enables PostgreSQL (SQLite used if unset) |
| `POSTGRES_USER` | — | PostgreSQL user |
| `POSTGRES_PASSWORD` | — | PostgreSQL password |
| `POSTGRES_HOST` | — | PostgreSQL host |
| `SELENIUM_HOST` | `localhost` | Selenium container hostname |
| `SECRET_KEY` | insecure default | Django secret key — always override in production |
| `ML_SKIP_WARMUP` | `0` | Set to `1` to skip model loading at startup |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for Next.js proxy |

---

## Testing

```bash
# Run all tests
python manage.py test

# Run with Docker
docker-compose exec web python manage.py test
```

The test suite covers:

- LinkedIn and Indeed HTML parser unit tests (no network, no DB)
- All REST API views: job list, detail, label, unlabeled, scrape trigger, scrape status, scrape history
- `_serialize_scrape_job` serializer
- 6 Hypothesis property-based tests:
  1. **ScrapeJob serialization round-trip** — all fields present and correct for any input
  2. **`jobs_found` null invariant** — always `null` for `pending` / `running` status
  3. **Thread completion stores job count** — `jobs_found` equals scraped list length
  4. **Thread failure stores error message** — `status=failed` and message preserved
  5. **Concurrent guard consistency** — 409 iff a running job exists
  6. **History ordering and limit** — at most 20 results, ordered by `created_at` desc

---

## CI/CD

Three jobs in `.github/workflows/ci.yml`, triggered on every push and PR to `main` or `develop`:

| Job | Depends on | What it does |
|---|---|---|
| **lint** | — | Runs `flake8` across the codebase |
| **test** | lint | Spins up a PostgreSQL service container, installs deps with `uv`, runs migrations, runs the full Django test suite |
| **docker-build** | lint | Validates the Docker image builds successfully using BuildKit cache |

---

## Design Decisions

**Template Method for scrapers** — `BaseScraper` owns all shared logic: browser lifecycle, retries, pagination, and anti-detection. Site-specific scrapers only implement `get_search_url()` and `parse_job_cards()`. Adding a new job site requires roughly 50 lines.

**Zero-shot first, fine-tune later** — BART-MNLI works out of the box with no labeled data. As labels accumulate via the labeling UI, `train_classifier` fine-tunes a smaller, faster `distilroberta-base`. The pipeline auto-switches to the fine-tuned model when it exists at the expected path.

**ModelCache singleton** — Transformer models are 200 MB–1.5 GB and take 10–30 s to load. The singleton ensures they load once per process. The `ml-worker` container is separate from `web` so model loading never blocks HTTP requests.

**ScrapeJob for progress tracking** — Scrapes run in a background thread. Rather than WebSockets or SSE, a simple DB record plus a polling endpoint keeps the architecture stateless and infrastructure-free. The frontend polls every 3 seconds with a 10-minute hard timeout.

**Separate ML worker container** — The `ml-worker` service has `shm_size: 2gb` (required by PyTorch data loaders) and mounts `~/.cache/huggingface` from the host so models are downloaded once and reused across container restarts.

**SQLite locally, PostgreSQL in Docker** — `settings.py` checks for the `POSTGRES_DB` environment variable. If absent, it falls back to SQLite. Same codebase, zero config for local development.
