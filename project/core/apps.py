from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
       from .job import start

       try:
            start()
            logger.info("✅ Scheduler started successfully.")
       except Exception as e:
            logger.error(f"❌ Scheduler failed to start: {e}")     