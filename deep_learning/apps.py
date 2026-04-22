from django.apps import AppConfig


class DeepLearningConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "deep_learning"
    verbose_name = "Deep Learning"

    def ready(self) -> None:
        """Register signals and warm model cache on startup."""
        import logging
        import os

        from deep_learning.pipeline import ModelCache

        logger = logging.getLogger(__name__)

        # Ensure signal receivers are registered.
        import deep_learning.signals  # noqa: F401

        # Startup warm-up can be disabled to speed local command execution.
        if os.environ.get("ML_SKIP_WARMUP", "0") == "1":
            logger.info("ML startup warmup skipped (ML_SKIP_WARMUP=1).")
            return

        try:
            ModelCache().initialize()
        except Exception as exc:
            logger.warning("ML models were not preloaded at startup: %s", exc)
