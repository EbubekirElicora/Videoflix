from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from video_app.models import Video
from video_app.selectors import clear_video_list_cache
from video_app.services import enqueue_video_processing


@receiver(post_save, sender=Video)
def handle_video_save(sender, instance, created, **kwargs):
    """Clear the cache and queue new videos for background processing."""
    clear_video_list_cache()

    if not created:
        return

    transaction.on_commit(lambda: enqueue_video_processing(instance.pk))


@receiver(post_delete, sender=Video)
def handle_video_delete(sender, instance, **kwargs):
    """Clear the cached video list after a video is deleted."""
    clear_video_list_cache()
