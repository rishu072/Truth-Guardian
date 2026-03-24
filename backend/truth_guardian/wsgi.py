"""
WSGI config for truth_guardian project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "truth_guardian.settings")

application = get_wsgi_application()
