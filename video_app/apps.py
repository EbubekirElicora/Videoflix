from importlib import import_module

from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "video_app"

    def ready(self):
        import_module("video_app.signals")
