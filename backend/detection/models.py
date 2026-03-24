from django.db import models


class DetectionResult(models.Model):
    """Stores every detection analysis for history / audit."""

    class AnalysisType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        SOCIAL = "social", "Social Media"

    class Verdict(models.TextChoices):
        LIKELY_TRUE = "Likely True", "Likely True"
        POSSIBLY_FAKE = "Possibly Fake", "Possibly Fake"
        UNVERIFIABLE = "Unverifiable", "Unverifiable"
        ERROR = "Error", "Error"

    analysis_type = models.CharField(
        max_length=10,
        choices=AnalysisType.choices,
        db_index=True,
    )
    input_content = models.TextField(
        help_text="The original text, claim, or URL submitted for analysis.",
    )
    title = models.CharField(max_length=512, blank=True, default="")
    truth_score = models.IntegerField(
        default=0,
        help_text="Confidence score from 0 to 100.",
    )
    verdict = models.CharField(
        max_length=30,
        choices=Verdict.choices,
        default=Verdict.UNVERIFIABLE,
    )
    reason = models.TextField(
        blank=True,
        default="",
        help_text="AI-generated explanation for the verdict.",
    )
    evidence_links = models.JSONField(
        default=list,
        blank=True,
        help_text="List of source URLs supporting the analysis.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Detection Result"
        verbose_name_plural = "Detection Results"

    def __str__(self):
        return f"[{self.analysis_type}] {self.verdict} ({self.truth_score}%) — {self.title[:60]}"
