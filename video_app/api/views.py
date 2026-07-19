from django.http import FileResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from video_app.api.serializers import VideoListSerializer
from video_app.selectors import get_video_list
from video_app.services import (
    get_video_manifest,
    get_video_segment,
)


class VideoListView(APIView):
    """Return the available videos to authenticated users."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = get_video_list()
        serializer = VideoListSerializer(
            videos,
            many=True,
            context={"request": request},
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class HLSManifestView(APIView):
    """Stream an HLS manifest for a supported video resolution."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        manifest_path = get_video_manifest(movie_id, resolution)
        return FileResponse(
            manifest_path.open("rb"),
            content_type="application/vnd.apple.mpegurl",
        )


class HLSSegmentView(APIView):
    """Stream a requested HLS transport-stream segment."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        segment_path = get_video_segment(
            movie_id,
            resolution,
            segment,
        )
        return FileResponse(
            segment_path.open("rb"),
            content_type="video/MP2T",
        )
