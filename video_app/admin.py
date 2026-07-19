from django.contrib import admin
from video_app.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "created_at",
    )
    list_filter = (
        "category",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "category",
    )
    readonly_fields = ("created_at",)
