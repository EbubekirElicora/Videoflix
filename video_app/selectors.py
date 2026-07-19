from django.core.cache import cache
from django.shortcuts import get_object_or_404

from video_app.models import Video


VIDEO_LIST_CACHE_KEY = "video_list"
VIDEO_LIST_CACHE_TIMEOUT = 300


def get_video_list():
    """Return the newest videos and cache the result for five minutes."""
    videos = cache.get(VIDEO_LIST_CACHE_KEY)

    if videos is None:
        videos = list(Video.objects.all().order_by("-created_at"))
        cache.set(
            VIDEO_LIST_CACHE_KEY,
            videos,
            VIDEO_LIST_CACHE_TIMEOUT,
        )

    return videos


def clear_video_list_cache():
    """Delete the cached video list after database changes."""
    cache.delete(VIDEO_LIST_CACHE_KEY)


def get_video_by_id(video_id):
    """Return the requested video or raise an HTTP 404 error."""
    return get_object_or_404(Video, pk=video_id)
