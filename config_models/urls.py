"""
URLs for config_models.
"""

from django.urls import re_path
from django.views.generic import TemplateView

urlpatterns = [
    re_path(r'', TemplateView.as_view(template_name="config_models/base.html")),
]
