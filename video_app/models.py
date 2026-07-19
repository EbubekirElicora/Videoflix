from django.db import models


class Video(models.Model):
    """Store video metadata, source files, and generated thumbnails."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    video_file = models.FileField(
        upload_to="videos/originals/",
    )
    thumbnail = models.FileField(
        upload_to="videos/thumbnails/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Return the video title as its readable representation."""
        return self.title
