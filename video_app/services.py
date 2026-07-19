import django_rq
from django.http import Http404

from video_app.selectors import get_video_by_id
from video_app.tasks import process_video
from video_app.utils import (
    get_manifest_path,
    get_segment_path,
    is_supported_resolution,
    is_valid_segment_name,
)


def enqueue_video_processing(video_id):
    """Add a video-processing task to the default RQ queue."""
    queue = django_rq.get_queue("default")
    return queue.enqueue(process_video, video_id)


def validate_hls_request(video_id, resolution):
    """Ensure that the video and requested resolution are valid."""
    get_video_by_id(video_id)

    if not is_supported_resolution(resolution):
        raise Http404("Video file not found.")


def get_video_manifest(video_id, resolution):
    """Return an existing HLS manifest path or raise HTTP 404."""
    validate_hls_request(video_id, resolution)
    manifest_path = get_manifest_path(video_id, resolution)

    if not manifest_path.is_file():
        raise Http404("Manifest not found.")

    return manifest_path


def get_video_segment(video_id, resolution, segment):
    """Return an existing HLS segment path or raise HTTP 404."""
    validate_hls_request(video_id, resolution)

    if not is_valid_segment_name(segment):
        raise Http404("Video segment not found.")

    segment_path = get_segment_path(video_id, resolution, segment)

    if not segment_path.is_file():
        raise Http404("Video segment not found.")

    return segment_path
