"""
Detection API views — Django REST Framework.

Endpoints:
  POST /api/detect/text/   — analyse text for misinformation
  POST /api/detect/image/  — analyse an uploaded image
  POST /api/detect/social/ — analyse a social media URL
"""

import os
import tempfile
import logging

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from PIL import Image

from .serializers import (
    TextDetectionSerializer,
    ImageDetectionSerializer,
    SocialDetectionSerializer,
)
from .services import analyze_text, analyze_image, analyze_social
from .models import DetectionResult

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _convert_to_supported_format(image_path: str) -> str:
    """Convert unsupported image formats to PNG."""
    _, ext = os.path.splitext(image_path)
    if ext.lower() in SUPPORTED_EXTENSIONS:
        return image_path

    try:
        img = Image.open(image_path)
        new_path = image_path.rsplit(".", 1)[0] + "_converted.png"
        img.save(new_path, format="PNG")
        return new_path
    except Exception as exc:
        raise RuntimeError(f"Failed to convert image: {exc}") from exc


def _save_result(analysis_type: str, input_content: str, result: dict) -> None:
    """Persist analysis result to the database."""
    try:
        DetectionResult.objects.create(
            analysis_type=analysis_type,
            input_content=input_content[:2000],
            title=result.get("title", ""),
            truth_score=result.get("truth_score", 0),
            verdict=result.get("verdict", "Error"),
            reason=result.get("reason", ""),
            evidence_links=result.get("evidence_links", []),
        )
    except Exception as exc:
        logger.error("Failed to save detection result: %s", exc)


# ── Text Detection ─────────────────────────────────────────────────────────────


@api_view(["POST"])
@parser_classes([JSONParser])
def detect_text(request):
    """POST /api/detect/text/ — Analyse a text claim for misinformation."""
    serializer = TextDetectionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    content = serializer.validated_data["content"]

    try:
        result = analyze_text(content)
        _save_result("text", content, result)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.exception("Text detection error")
        return Response(
            {"error": f"Analysis failed: {str(exc)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Image Detection ────────────────────────────────────────────────────────────


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def detect_image(request):
    """POST /api/detect/image/ — Analyse an uploaded image for misinformation."""
    serializer = ImageDetectionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    uploaded_file = serializer.validated_data["file"]
    query = serializer.validated_data.get("query", "")

    ext = os.path.splitext(uploaded_file.name)[-1] or ".jpg"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            image_path = tmp.name

        image_path = _convert_to_supported_format(image_path)
        result = analyze_image(image_path, query)
        _save_result("image", query or uploaded_file.name, result)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.exception("Image detection error")
        return Response(
            {"error": f"Analysis failed: {str(exc)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        # Clean up temp files
        try:
            if "image_path" in dir():
                os.unlink(image_path)
        except OSError:
            pass


# ── Social Media Detection ─────────────────────────────────────────────────────


@api_view(["POST"])
@parser_classes([JSONParser])
def detect_social(request):
    """POST /api/detect/social/ — Analyse a social media post for misinformation."""
    serializer = SocialDetectionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    url = serializer.validated_data["url"]
    claim = serializer.validated_data.get("claim", "")

    try:
        result = analyze_social(url, claim)
        _save_result("social", f"{url} | {claim}", result)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.exception("Social detection error")
        return Response(
            {"error": f"Analysis failed: {str(exc)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
