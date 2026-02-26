# 🔍 JobsFinder

A Django-powered job aggregation platform that scrapes job listings from the web and uses deep learning models to classify and extract insights from job descriptions.

## 🏗️ Architecture

| Module | Technology | Purpose |
|--------|-----------|---------|
| **Backend** | Django 6.0 / Python 3.12 | REST API & data management |
| **Scraping** | Selenium + BeautifulSoup | Headless browser job scraping |
| **Deep Learning** | HuggingFace Transformers + PyTorch | Job classification & NER |
| **Database** | PostgreSQL 15 | Persistent storage |
| **Containers** | Docker Compose | Service orchestration |

## 🚀 Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- (Optional) Python 3.12+ and [uv](https://github.com/astral-sh/uv) for local dev

### Run with Docker

```bash
# Build and start all services
docker-compose up --build

# In another terminal, run migrations
docker-compose exec web python manage.py migrate

# Test the scraper
docker-compose exec web python manage.py test_scraper
```

The app will be available at **http://localhost:8000**.

### Run Locally (without Docker)

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# Install dependencies
uv pip install -r pyproject.toml

# Run migrations (uses SQLite locally)
python manage.py migrate

# Start the dev server
python manage.py runserver
```

## 📁 Project Structure

```
jobsFinder/
├── backend/            # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── scraping/           # Web scraping module
│   ├── models.py       # JobListing model
│   ├── scraper.py      # Selenium scraper
│   └── management/     # Django management commands
├── deep_learning/      # ML/NLP module (WIP)
├── docker-compose.yml  # Docker service definitions
├── Dockerfile          # App container image
├── pyproject.toml      # Python dependencies
└── MODULE_TASKS.md     # Development task tracker
```

## 🧪 Testing

```bash
# Run Django tests
python manage.py test

# Run with Docker
docker-compose exec web python manage.py test
```

## 🔄 CI/CD

This project uses **GitHub Actions** for continuous integration:

- **Lint** — Runs `flake8` on every push/PR
- **Test** — Runs Django test suite with a PostgreSQL service container
- **Docker Build** — Validates the Docker image builds successfully

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for details.

## 📝 License

This project is for personal/educational use.
