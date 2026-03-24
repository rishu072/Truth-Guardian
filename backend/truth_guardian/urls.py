"""
Root URL configuration for truth_guardian project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("detection.urls")),
]
