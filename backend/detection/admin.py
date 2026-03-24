from django.contrib import admin
from .models import DetectionResult


@admin.register(DetectionResult)
class DetectionResultAdmin(admin.ModelAdmin):
    list_display = ("analysis_type", "verdict", "truth_score", "title", "created_at")
    list_filter = ("analysis_type", "verdict", "created_at")
    search_fields = ("title", "input_content", "reason")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
