"""
ConfigurationModel Admin Module Test Cases
"""
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.test import TestCase
from example.models import ExampleKeyedConfig

from config_models import admin
from config_models.models import ConfigurationModel

User = get_user_model()


class AdminTestCaseMixin:
    """
    Provide a request factory method.
    """

    def get_request(self):
        request = HttpRequest()
        request.session = "session"
        request._messages = FallbackStorage(request)  # pylint: disable=protected-access
        return request


class AdminTestCase(TestCase, AdminTestCaseMixin):
    """
    Test Case module for ConfigurationModel Admin
    """

    def setUp(self):
        super().setUp()
        self.conf_admin = admin.ConfigurationModelAdmin(ConfigurationModel, AdminSite())

    def test_default_fields(self):
        """
        Test: checking fields
        """
        request = self.get_request()
        self.assertEqual(
            list(self.conf_admin.get_form(request).base_fields), ["enabled"]
        )


class KeyedAdminTestCase(TestCase, AdminTestCaseMixin):
    """
    Test case module for KeyedConfigurationModelAdmin.
    """

    def get_edit_link(self):
        """
        Return an edit link from a KeyedConfigurationModelAdmin. Patch the `reverse`
        and `_` methods to modify the return value.
        """
        conf_admin = admin.KeyedConfigurationModelAdmin(ExampleKeyedConfig, AdminSite())
        request = self.get_request()
        ExampleKeyedConfig.objects.create(user=User.objects.create())
        config = conf_admin.get_queryset(request)[0]
        return conf_admin.edit_link(config)

    def test_edit_link(self):
        with patch.object(admin, "reverse", return_value="http://google.com"):
            self.assertEqual(
                '<a href="http://google.com?source=1">Update</a>', self.get_edit_link(),
            )

    def test_edit_link_xss_url(self):
        with patch.object(
                admin, "reverse", return_value='"><script>console.log("xss!")</script>'
        ):
            edit_link = self.get_edit_link()

        self.assertNotIn(
            "<script>", edit_link,
        )
        self.assertIn(
            "&lt;script&gt;", edit_link,
        )

    def test_edit_link_xss_translation(self):
        with patch.object(admin, "reverse", return_value=""):
            with patch.object(
                    admin, "_", return_value='<script>console.log("xss!")</script>'
            ):
                edit_link = self.get_edit_link()

        self.assertNotIn(
            "<script>", edit_link,
        )
        self.assertIn(
            "&lt;script&gt;", edit_link,
        )
