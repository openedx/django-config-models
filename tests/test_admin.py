"""
ConfigurationModel Admin Module Test Cases
"""

from __future__ import unicode_literals

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.test import TestCase

from config_models.admin import ConfigurationModelAdmin
from config_models.models import ConfigurationModel


class AdminTestCase(TestCase):
    """
    Test Case module for ConfigurationModel Admin
    """
    def setUp(self):
        super(AdminTestCase, self).setUp()
        self.request = HttpRequest()
        self.conf_admin = ConfigurationModelAdmin(ConfigurationModel, AdminSite())
        self.request.session = 'session'
        self.request._messages = FallbackStorage(self.request)  # pylint: disable=protected-access

    def test_default_fields(self):
        """
        Test: checking fields
        """
        self.assertEqual(
            list(self.conf_admin.get_form(self.request).base_fields),
            ['enabled']
        )
