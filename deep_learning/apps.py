from django.apps import AppConfig


class DeepLearningConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "deep_learning"
    verbose_name = "Deep Learning"

    # Management commands that never need ML models loaded.
    _SKIP_WARMUP_COMMANDS = {
        "migrate", "makemigrations", "collectstatic", "createsuperuser",
        "shell", "dbshell", "showmigrations", "sqlmigrate", "check",
        "flush", "inspectdb", "test",
    }

    def ready(self) -> None:
        """Register signals and warm model cache on startup."""
        import logging
        import os
        import sys

        from deep_learning.pipeline import ModelCache

        logger = logging.getLogger(__name__)

        # Ensure signal receivers are registered.
        import deep_learning.signals  # noqa: F401

        # Startup warm-up can be disabled explicitly via env var.
        if os.environ.get("ML_SKIP_WARMUP", "0") == "1":
            logger.info("ML startup warmup skipped (ML_SKIP_WARMUP=1).")
            return

        # Auto-skip warmup for management commands that don't need ML models.
        if len(sys.argv) >= 2 and sys.argv[1] in self._SKIP_WARMUP_COMMANDS:
            logger.info("ML startup warmup skipped for '%s' command.", sys.argv[1])
            return

        try:
            ModelCache().initialize()
        except Exception as exc:
            logger.warning("ML models were not preloaded at startup: %s", exc)
