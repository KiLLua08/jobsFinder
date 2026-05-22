# 📖 How to Use JobsFinder

## Overview

JobsFinder is a full-stack app with 3 layers:
- **Django backend** — REST API, scraping engine, ML pipeline
- **Next.js frontend** — UI at `http://localhost:3000`
- **Docker Compose** — orchestrates Postgres, Selenium Chrome, pgAdmin, and both apps

---

## 1. First-Time Setup

### Prerequisites
- Docker Desktop running
- A `.env` file in the project root (already present)

The `.env` must contain:
```
POSTGRES_PASSWORD=yourpassword
PGADMIN_MAIL=admin@admin.com
PGADMIN_PASSWORD=yourpassword
```

### Start everything
```bash
docker-compose up --build
```

Then in a second terminal, run migrations:
```bash
docker-compose exec web python manage.py migrate
```

Services available after startup:

| Service | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend API (Django) | http://localhost:8000 |
| pgAdmin (DB viewer) | http://localhost:5050 |
| Selenium Chrome VNC | http://localhost:7900 |

---

## 2. Scraping Jobs

### Via CLI (recommended)
```bash
# Scrape LinkedIn for "Data Scientist" (3 pages)
docker-compose exec web python manage.py scrape --site linkedin --query "Data Scientist"

# Scrape Indeed
docker-compose exec web python manage.py scrape --site indeed --query "Python Developer"

# Scrape both sites at once
docker-compose exec web python manage.py scrape --site all --query "ML Engineer" --pages 5

# Preview without saving to DB
docker-compose exec web python manage.py scrape --site linkedin --query "Django" --no-save

# Clear DB first, then scrape fresh
docker-compose exec web python manage.py scrape --site all --query "Software Engineer" --clear-before
```

### Via Frontend
Go to http://localhost:3000/scrape — enter a query and click "Start Scraping".

> ⚠️ The frontend scrape button currently simulates progress only. Use the CLI command above for real scraping.

---

## 3. Viewing Jobs

### Frontend
Go to http://localhost:3000/jobs

- Search by title using the search bar
- Filter by Relevant / Irrelevant using the dropdown
- Click a job title to see full details
- Click the external link icon to open the original posting

### API
```bash
# List all jobs
curl http://localhost:8000/api/jobs/

# Search by title
curl "http://localhost:8000/api/jobs/?search=python"

# Filter relevant only
curl "http://localhost:8000/api/jobs/?relevant=true"

# Get a specific job
curl http://localhost:8000/api/jobs/1/
```

---

## 4. Running the ML Pipeline

The ML pipeline classifies jobs as relevant/irrelevant and extracts technical skills using HuggingFace models.

> ⚠️ First run downloads ~1GB of models. Use the `ml-worker` container to avoid slowing down the web server.

### Analyze all unprocessed jobs
```bash
# Using the new pipeline (recommended)
docker-compose exec ml-worker python manage.py test_ml_pipeline

# Using the legacy analyzer
docker-compose exec ml-worker python manage.py analyze_jobs
```

### Process via API
```bash
# Process a batch of unprocessed jobs
curl -X POST http://localhost:8000/api/ml/process-batch/ \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'

# Classify a single job description
curl -X POST http://localhost:8000/api/ml/classify/ \
  -H "Content-Type: application/json" \
  -d '{"description": "We are looking for a Python developer with Django experience..."}'

# Check ML pipeline health
curl http://localhost:8000/api/ml/health/

# Get processing stats
curl http://localhost:8000/api/ml/stats/
```

### Via Frontend
- **Classify Demo** → http://localhost:3000/classify — paste any job description and get instant AI analysis
- **Dashboard** → http://localhost:3000/dashboard — see processing stats and model status

---

## 5. Human Labeling (for ML Training)

Label jobs as relevant or irrelevant to build a training dataset for fine-tuning.

### Via Frontend
Go to http://localhost:3000/label — jobs are shown one at a time, click 👍 Relevant or 👎 Irrelevant.

### Via API
```bash
curl -X POST http://localhost:8000/api/jobs/1/label/ \
  -H "Content-Type: application/json" \
  -d '{"is_relevant": true}'
```

---

## 6. Training a Custom Model

Once you have labeled enough jobs (recommended: 100+):

```bash
# Step 1: Export labeled data to JSONL
docker-compose exec ml-worker python manage.py export_training_data

# Step 2: Dry run to verify data loads correctly
docker-compose exec ml-worker python manage.py train_classifier --dry_run

# Step 3: Run actual training (requires GPU for reasonable speed)
docker-compose exec ml-worker python manage.py train_classifier
```

The fine-tuned model is saved to `deep_learning/saved_models/classifier_v1/` and is automatically picked up by the pipeline on next use.

---

## 7. Dashboard

Go to http://localhost:3000/dashboard to see:
- Total jobs scraped
- How many have been ML-processed
- How many are classified as relevant
- ML model load status (classifier + NER)

---

## 8. Database Access

### pgAdmin
1. Go to http://localhost:5050
2. Login with your `PGADMIN_MAIL` and `PGADMIN_PASSWORD` from `.env`
3. Add a new server: host = `db`, port = `5432`, user = `postgres`

### Django Admin
```bash
# Create a superuser first
docker-compose exec web python manage.py createsuperuser
```
Then go to http://localhost:8000/admin

---

## 9. Local Development (without Docker)

```bash
# Install dependencies
uv venv && .venv\Scripts\activate
uv pip install -r pyproject.toml

# Run migrations (uses SQLite locally)
python manage.py migrate

# Start backend
python manage.py runserver

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

> Note: Scraping locally requires a Selenium server running at `localhost:4444`. Start it with:
> `docker run -p 4444:4444 selenium/standalone-chrome`

---

## 10. API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs/` | List jobs (supports `?search=`, `?relevant=`, `?skill=`) |
| GET | `/api/jobs/<id>/` | Get single job |
| POST | `/api/jobs/<id>/label/` | Set human label `{"is_relevant": true}` |
| GET | `/api/jobs/unlabeled/` | Get 50 random unlabeled jobs |
| POST | `/api/ml/classify/` | Classify a description `{"description": "..."}` |
| POST | `/api/ml/process-batch/` | Process unprocessed jobs `{"limit": 10}` |
| GET | `/api/ml/stats/` | Get processing statistics |
| GET | `/api/ml/health/` | Check model load status |
