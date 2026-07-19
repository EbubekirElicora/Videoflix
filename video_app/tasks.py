from django.db import close_old_connections

from video_app.models import Video
from video_app.utils import (
    HLS_RESOLUTIONS,
    build_hls_command,
    build_thumbnail_command,
    create_directory,
    get_hls_directory,
    get_thumbnail_name,
    get_thumbnail_path,
    run_ffmpeg,
)


def generate_thumbnail(video):
    """Generate and store a thumbnail for the supplied video."""
    output_path = get_thumbnail_path(video.id)
    create_directory(output_path.parent)
    command = build_thumbnail_command(video.video_file.path, output_path)
    run_ffmpeg(command)
    video.thumbnail.name = get_thumbnail_name(video.id)
    video.save(update_fields=["thumbnail"])


def generate_hls_version(video, resolution, height):
    """Generate one HLS version for the requested resolution."""
    output_directory = get_hls_directory(video.id, resolution)
    create_directory(output_directory)
    command = build_hls_command(video.video_file.path, height)
    run_ffmpeg(command, output_directory)


def generate_hls_versions(video):
    """Generate every supported HLS resolution for a video."""
    for resolution, height in HLS_RESOLUTIONS.items():
        generate_hls_version(video, resolution, height)


def process_video(video_id):
    """Process a video in the background using a fresh DB connection."""
    close_old_connections()

    try:
        video = Video.objects.get(pk=video_id)
        generate_thumbnail(video)
        generate_hls_versions(video)
    finally:
        close_old_connections()
