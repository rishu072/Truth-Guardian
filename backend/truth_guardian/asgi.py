"""
ASGI config for truth_guardian project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "truth_guardian.settings")

application = get_asgi_application()
