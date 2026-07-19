"""Provide file-path and FFmpeg helpers for video processing."""

import re
import subprocess
from pathlib import Path

from django.conf import settings


HLS_RESOLUTIONS = {
    "480p": 480,
    "720p": 720,
    "1080p": 1080,
}

HLS_VIDEO_OPTIONS = (
    "-c:v",
    "libx264",
    "-preset",
    "medium",
    "-crf",
    "23",
)

HLS_AUDIO_OPTIONS = (
    "-c:a",
    "aac",
    "-b:a",
    "128k",
)

HLS_OUTPUT_OPTIONS = (
    "-hls_time",
    "10",
    "-hls_playlist_type",
    "vod",
    "-hls_segment_filename",
    "segment_%03d.ts",
    "index.m3u8",
)


def get_hls_directory(video_id, resolution):
    """Return the directory for one video's HLS resolution."""
    return Path(settings.MEDIA_ROOT) / "videos" / "hls" / str(video_id) / resolution


def get_manifest_path(video_id, resolution):
    """Return the path to an HLS manifest file."""
    return get_hls_directory(video_id, resolution) / "index.m3u8"


def get_segment_path(video_id, resolution, segment):
    """Return the path to a requested HLS segment file."""
    return get_hls_directory(video_id, resolution) / segment


def is_valid_segment_name(segment):
    """Check whether a segment name matches the expected format."""
    return re.fullmatch(r"segment_\d+\.ts", segment) is not None


def is_supported_resolution(resolution):
    """Check whether the requested HLS resolution is supported."""
    return resolution in HLS_RESOLUTIONS


def get_thumbnail_path(video_id):
    """Return the absolute path for a generated thumbnail."""
    return Path(settings.MEDIA_ROOT) / "videos" / "thumbnails" / f"{video_id}.jpg"


def get_thumbnail_name(video_id):
    """Return the thumbnail path stored in the database field."""
    return f"videos/thumbnails/{video_id}.jpg"


def create_directory(directory):
    """Create a directory and all missing parent directories."""
    directory.mkdir(parents=True, exist_ok=True)


def build_thumbnail_command(input_path, output_path):
    """Build the FFmpeg command used to generate a thumbnail."""
    return [
        "ffmpeg",
        "-y",
        "-ss",
        "00:00:01",
        "-i",
        str(input_path),
        "-frames:v",
        "1",
        str(output_path),
    ]


def build_hls_command(input_path, height):
    """Build the FFmpeg command used to generate an HLS version."""
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        f"scale=-2:{height}",
        *HLS_VIDEO_OPTIONS,
        *HLS_AUDIO_OPTIONS,
        *HLS_OUTPUT_OPTIONS,
    ]


def run_ffmpeg(command, working_directory=None):
    """Execute an FFmpeg command and raise an error if it fails."""
    subprocess.run(
        command,
        cwd=working_directory,
        check=True,
    )
