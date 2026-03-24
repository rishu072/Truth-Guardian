from django.urls import path
from . import views

urlpatterns = [
    path("detect/text/", views.detect_text, name="detect-text"),
    path("detect/image/", views.detect_image, name="detect-image"),
    path("detect/social/", views.detect_social, name="detect-social"),
]
