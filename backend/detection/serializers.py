from rest_framework import serializers


class TextDetectionSerializer(serializers.Serializer):
    """Validates input for text-based fake news detection."""
    content = serializers.CharField(
        min_length=10,
        max_length=10000,
        help_text="The news text / claim to verify.",
    )


class ImageDetectionSerializer(serializers.Serializer):
    """Validates input for image-based fake news detection."""
    file = serializers.ImageField(
        help_text="The image file to analyze.",
    )
    query = serializers.CharField(
        required=False,
        default="Check if this image depicts a real or fake incident.",
        max_length=2000,
        help_text="Optional claim or description of the image.",
    )


class SocialDetectionSerializer(serializers.Serializer):
    """Validates input for social media post detection."""
    url = serializers.URLField(
        help_text="Social media post URL to analyze.",
    )
    claim = serializers.CharField(
        required=False,
        default="Verify the claim and check if it is true.",
        max_length=2000,
        help_text="Optional claim to verify against the post.",
    )


class DetectionResultSerializer(serializers.Serializer):
    """Serializes the AI detection response."""
    title = serializers.CharField()
    truth_score = serializers.IntegerField(min_value=0, max_value=100)
    verdict = serializers.CharField()
    reason = serializers.CharField()
    evidence_links = serializers.ListField(
        child=serializers.URLField(allow_blank=True),
        allow_empty=True,
    )
