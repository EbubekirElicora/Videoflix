from rest_framework import serializers
from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """Serialize video metadata for the authenticated video list."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        )

    def get_thumbnail_url(self, video):
        """Return an absolute thumbnail URL when a thumbnail exists."""
        if not video.thumbnail:
            return None

        request = self.context.get("request")
        thumbnail_url = video.thumbnail.url

        if request is None:
            return thumbnail_url

        return request.build_absolute_uri(thumbnail_url)
