"""
Tests of ConfigurationModel
"""
from unittest import mock

import ddt
from django.contrib.auth import get_user_model
from edx_django_utils.cache.utils import CachedResponse
from example.models import (ExampleConfig, ExampleKeyedConfig,
                            ManyToManyExampleConfig)
from freezegun import freeze_time
from rest_framework.test import APIRequestFactory

from config_models.views import ConfigurationModelCurrentAPIView

from .utils import CacheIsolationTestCase

User = get_user_model()


class ConfigurationModelTests(CacheIsolationTestCase):
    """
    Tests of ConfigurationModel
    """
    def setUp(self):
        super().setUp()
        self.user = User()
        self.user.save()

    def test_cache_key_name(self):
        self.assertEqual(
            ExampleConfig.cache_key_name(),
            'configuration/ExampleConfig/current'
        )

    def test_no_config_empty_cache(self):
        # First time reads from the database
        with self.assertNumQueries(1):
            current = ExampleConfig.current()
            self.assertEqual(current.int_field, 10)
            self.assertEqual(current.string_field, '')

        # Follow-on request reads from cache with no database request.
        with self.assertNumQueries(0):
            cached_current = ExampleConfig.current()
            self.assertEqual(cached_current.int_field, 10)
            self.assertEqual(cached_current.string_field, '')

    @mock.patch('config_models.models.TieredCache.get_cached_response')
    def test_config_with_cached_response_value_none(self, mock_cached_response):
        mock_cached_response.return_value = CachedResponse(is_found=True, key='test-key', value=None)
        # First time reads from the database
        with self.assertNumQueries(1):
            current = ExampleConfig.current()
            self.assertEqual(current.int_field, 10)
            self.assertEqual(current.string_field, '')

        # Follow-on request reads from database instead of cache as cache value will be None.
        with self.assertNumQueries(1):
            cached_current = ExampleConfig.current()
            self.assertEqual(cached_current.int_field, 10)
            self.assertEqual(cached_current.string_field, '')

    def test_config_ordering(self):
        with freeze_time('2012-01-01'):
            first = ExampleConfig(changed_by=self.user)
            first.string_field = 'first'
            first.save()

        second = ExampleConfig(changed_by=self.user)
        second.string_field = 'second'
        second.save()

        self.assertEqual(ExampleConfig.current().string_field, 'second')

    def test_cache_set(self):
        # Nothing is cached, so we take a database hit for this.
        with self.assertNumQueries(1):
            default = ExampleConfig.current()
            self.assertEqual(default.string_field, '')

        first = ExampleConfig(changed_by=self.user)
        first.string_field = 'first'
        first.save()

        # The save() call above should have invalidated the cache, so we expect
        # to see a query to get the current config value.
        with self.assertNumQueries(1):
            current = ExampleConfig.current()
            self.assertEqual(current.string_field, 'first')

    def test_active_annotation(self):
        with freeze_time('2012-01-01'):
            ExampleConfig.objects.create(string_field='first')

        ExampleConfig.objects.create(string_field='second')

        rows = ExampleConfig.objects.with_active_flag().order_by('-change_date')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].string_field, 'second')
        self.assertEqual(rows[0].is_active, True)
        self.assertEqual(rows[1].string_field, 'first')
        self.assertEqual(rows[1].is_active, False)

    def test_keyed_active_annotation(self):
        with freeze_time('2012-01-01'):
            ExampleKeyedConfig.objects.create(left='left', right='right', user=self.user, string_field='first')

        ExampleKeyedConfig.objects.create(left='left', right='right', user=self.user, string_field='second')

        rows = ExampleKeyedConfig.objects.with_active_flag().order_by('-change_date')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].string_field, 'second')
        self.assertEqual(rows[0].is_active, True)
        self.assertEqual(rows[1].string_field, 'first')
        self.assertEqual(rows[1].is_active, False)

    def test_always_insert(self):
        config = ExampleConfig(changed_by=self.user, string_field='first')
        config.save()
        config.string_field = 'second'
        config.save()

        self.assertEqual(2, ExampleConfig.objects.all().count())

    def test_equality(self):
        config = ExampleConfig(changed_by=self.user, string_field='first')
        config.save()

        self.assertTrue(ExampleConfig.equal_to_current({"string_field": "first"}))
        self.assertTrue(ExampleConfig.equal_to_current({"string_field": "first", "enabled": False}))
        self.assertTrue(ExampleConfig.equal_to_current({"string_field": "first", "int_field": 10}))

        self.assertFalse(ExampleConfig.equal_to_current({"string_field": "first", "enabled": True}))
        self.assertFalse(ExampleConfig.equal_to_current({"string_field": "first", "int_field": 20}))
        self.assertFalse(ExampleConfig.equal_to_current({"string_field": "second"}))

        self.assertFalse(ExampleConfig.equal_to_current({}))

    def test_equality_custom_fields_to_ignore(self):
        config = ExampleConfig(changed_by=self.user, string_field='first')
        config.save()

        # id, change_date, and changed_by will all be different for a newly created entry
        self.assertTrue(ExampleConfig.equal_to_current({"string_field": "first"}))
        self.assertFalse(
            ExampleConfig.equal_to_current({"string_field": "first"}, fields_to_ignore=("change_date", "changed_by"))
        )
        self.assertFalse(
            ExampleConfig.equal_to_current({"string_field": "first"}, fields_to_ignore=("id", "changed_by"))
        )
        self.assertFalse(
            ExampleConfig.equal_to_current({"string_field": "first"}, fields_to_ignore=("change_date", "id"))
        )

        # Test the ability to ignore a different field ("int_field").
        self.assertFalse(ExampleConfig.equal_to_current({"string_field": "first", "int_field": 20}))
        self.assertTrue(
            ExampleConfig.equal_to_current(
                {"string_field": "first", "int_field": 20},
                fields_to_ignore=("id", "change_date", "changed_by", "int_field")
            )
        )

    def test_equality_ignores_many_to_many(self):
        config = ManyToManyExampleConfig(changed_by=self.user, string_field='first')
        config.save()

        second_user = User(username="second_user")
        second_user.save()
        config.many_user_field.add(second_user)
        config.save()

        # The many-to-many field is ignored in comparison.
        self.assertTrue(
            ManyToManyExampleConfig.equal_to_current({"string_field": "first", "many_user_field": "removed"})
        )


@ddt.ddt
class KeyedConfigurationModelTests(CacheIsolationTestCase):
    """
    Tests for ``ConfigurationModels`` with keyed configuration.
    """
    def setUp(self):
        super().setUp()
        self.user = User()
        self.user.save()

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_cache_key_name(self, left, right):
        self.assertEqual(
            ExampleKeyedConfig.cache_key_name(left, right, self.user),
            f'configuration/ExampleKeyedConfig/current/{left},{right},{self.user}'
        )

    @ddt.data(
        ((), 'left,right,user'),
        (('left', 'right'), 'left,right'),
        (('left', ), 'left')
    )
    @ddt.unpack
    def test_key_values_cache_key_name(self, args, expected_key):
        self.assertEqual(
            ExampleKeyedConfig.key_values_cache_key_name(*args),
            f'configuration/ExampleKeyedConfig/key_values/{expected_key}')

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_no_config_empty_cache(self, left, right):
        # First time, it comes from the database.
        with self.assertNumQueries(1):
            current = ExampleKeyedConfig.current(left, right, self.user)
            self.assertEqual(current.int_field, 10)
            self.assertEqual(current.string_field, '')

        # Second time, it should come from cache.
        with self.assertNumQueries(0):
            current = ExampleKeyedConfig.current(left, right, self.user)
            self.assertEqual(current.int_field, 10)
            self.assertEqual(current.string_field, '')

    def test_config_ordering(self):
        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(
                changed_by=self.user,
                left='left_a',
                right='right_a',
                string_field='first_a',
                user=self.user,
            ).save()

            ExampleKeyedConfig(
                changed_by=self.user,
                left='left_b',
                right='right_b',
                string_field='first_b',
                user=self.user,
            ).save()

        ExampleKeyedConfig(
            changed_by=self.user,
            left='left_a',
            right='right_a',
            string_field='second_a',
            user=self.user,
        ).save()
        ExampleKeyedConfig(
            changed_by=self.user,
            left='left_b',
            right='right_b',
            string_field='second_b',
            user=self.user,
        ).save()

        self.assertEqual(ExampleKeyedConfig.current('left_a', 'right_a', self.user).string_field, 'second_a')
        self.assertEqual(ExampleKeyedConfig.current('left_b', 'right_b', self.user).string_field, 'second_b')

    def test_cache_set(self):
        with self.assertNumQueries(1):
            default = ExampleConfig.current('left', 'right', self.user)
            self.assertEqual(default.string_field, '')

        first = ExampleKeyedConfig(
            changed_by=self.user,
            left='left',
            right='right',
            user=self.user,
            string_field='first',
        )
        first.save()

        # Cache is invalidated by the save above, so another query is made.
        with self.assertNumQueries(1):
            ExampleKeyedConfig.current('left', 'right', self.user)

    def test_key_values(self):
        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(left='left_a', right='right_a', user=self.user, changed_by=self.user).save()
            ExampleKeyedConfig(left='left_b', right='right_b', user=self.user, changed_by=self.user).save()

        ExampleKeyedConfig(left='left_a', right='right_a', user=self.user, changed_by=self.user).save()
        ExampleKeyedConfig(left='left_b', right='right_b', user=self.user, changed_by=self.user).save()

        unique_key_pairs = ExampleKeyedConfig.key_values()
        self.assertEqual(len(unique_key_pairs), 2)
        self.assertEqual(
            set(unique_key_pairs),
            {('left_a', 'right_a', self.user.id), ('left_b', 'right_b', self.user.id)}
        )
        unique_left_keys = ExampleKeyedConfig.key_values('left', flat=True)
        self.assertEqual(len(unique_left_keys), 2)
        self.assertEqual(set(unique_left_keys), {'left_a', 'left_b'})

    def test_key_string_values(self):
        """ Ensure str() vs unicode() doesn't cause duplicate cache entries """
        ExampleKeyedConfig(
            left='left',
            right='\N{RIGHT ANGLE BRACKET}\N{SNOWMAN}',
            enabled=True,
            int_field=10,
            user=self.user,
            changed_by=self.user
        ).save()

        entry = ExampleKeyedConfig.current('left', '\N{RIGHT ANGLE BRACKET}\N{SNOWMAN}', self.user)
        self.assertEqual(entry.int_field, 10)

        entry = ExampleKeyedConfig.current('left', '\N{RIGHT ANGLE BRACKET}\N{SNOWMAN}', self.user)
        self.assertEqual(entry.int_field, 10)

    def test_current_set(self):
        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(left='left_a', right='right_a', int_field=0, user=self.user, changed_by=self.user).save()
            ExampleKeyedConfig(left='left_b', right='right_b', int_field=0, user=self.user, changed_by=self.user).save()

        ExampleKeyedConfig(left='left_a', right='right_a', int_field=1, user=self.user, changed_by=self.user).save()
        ExampleKeyedConfig(left='left_b', right='right_b', int_field=2, user=self.user, changed_by=self.user).save()

        queryset = ExampleKeyedConfig.objects.current_set()
        self.assertEqual(len(queryset.all()), 2)
        self.assertEqual(
            set(queryset.order_by('int_field').values_list('int_field', flat=True)),
            {1, 2}
        )

    def test_active_annotation(self):
        with freeze_time('2012-01-01'):
            ExampleKeyedConfig.objects.create(left='left_a', right='right_a', user=self.user, string_field='first')
            ExampleKeyedConfig.objects.create(left='left_b', right='right_b', user=self.user, string_field='first')

        ExampleKeyedConfig.objects.create(left='left_a', right='right_a', user=self.user, string_field='second')

        rows = ExampleKeyedConfig.objects.with_active_flag()
        self.assertEqual(len(rows), 3)
        for row in rows:
            if row.left == 'left_a':
                self.assertEqual(row.is_active, row.string_field == 'second')
            else:
                self.assertEqual(row.left, 'left_b')
                self.assertEqual(row.string_field, 'first')
                self.assertEqual(row.is_active, True)

    def test_equality(self):
        config1 = ExampleKeyedConfig(left='left_a', right='right_a', int_field=1, user=self.user, changed_by=self.user)
        config1.save()

        config2 = ExampleKeyedConfig(
            left='left_b',
            right='right_b',
            int_field=2,
            user=self.user,
            changed_by=self.user,
            enabled=True,
        )
        config2.save()

        config3 = ExampleKeyedConfig(left='left_c', user=self.user, changed_by=self.user)
        config3.save()

        self.assertTrue(
            ExampleKeyedConfig.equal_to_current({
                "left": "left_a",
                "right": "right_a",
                "int_field": 1,
                "user": self.user
            })
        )
        self.assertTrue(
            ExampleKeyedConfig.equal_to_current({
                "left": "left_b",
                "right": "right_b",
                "int_field": 2,
                "user": self.user,
                "enabled": True
            })
        )
        self.assertTrue(
            ExampleKeyedConfig.equal_to_current({"left": "left_c", "user": self.user})
        )

        self.assertFalse(
            ExampleKeyedConfig.equal_to_current(
                {"left": "left_a", "right": "right_a", "user": self.user, "int_field": 1, "string_field": "foo"}
            )
        )
        self.assertFalse(
            ExampleKeyedConfig.equal_to_current({"left": "left_a", "user": self.user, "int_field": 1})
        )
        self.assertFalse(
            ExampleKeyedConfig.equal_to_current({
                "left": "left_b",
                "right": "right_b",
                "user": self.user,
                "int_field": 2,
            })
        )
        self.assertFalse(
            ExampleKeyedConfig.equal_to_current({"left": "left_c", "user": self.user, "int_field": 11})
        )

        self.assertFalse(ExampleKeyedConfig.equal_to_current({"user": self.user}))


@ddt.ddt
class ConfigurationModelAPITests(CacheIsolationTestCase):
    """
    Tests for the configuration model API.
    """
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@example.com',
            password='test_pass',
        )
        self.user.is_superuser = True
        self.user.save()
        self.current_view = ConfigurationModelCurrentAPIView.as_view(model=ExampleConfig)

    def test_insert(self):
        self.assertEqual("", ExampleConfig.current().string_field)

        request = self.factory.post('/config/ExampleConfig', {"string_field": "string_value"})
        request.user = self.user
        __ = self.current_view(request)

        self.assertEqual("string_value", ExampleConfig.current().string_field)
        self.assertEqual(self.user, ExampleConfig.current().changed_by)

    def test_multiple_inserts(self):
        for i in range(3):
            self.assertEqual(i, ExampleConfig.objects.all().count())

            request = self.factory.post('/config/ExampleConfig', {"string_field": str(i)})
            request.user = self.user
            response = self.current_view(request)
            self.assertEqual(201, response.status_code)

            self.assertEqual(i + 1, ExampleConfig.objects.all().count())
            self.assertEqual(str(i), ExampleConfig.current().string_field)

    def test_get_current(self):
        request = self.factory.get('/config/ExampleConfig')
        request.user = self.user
        response = self.current_view(request)
        self.assertEqual('', response.data['string_field'])
        self.assertEqual(10, response.data['int_field'])
        self.assertEqual(None, response.data['changed_by'])
        self.assertEqual(False, response.data['enabled'])
        self.assertEqual(None, response.data['change_date'])

        ExampleConfig(string_field='string_value', int_field=20).save()

        response = self.current_view(request)
        self.assertEqual('string_value', response.data['string_field'])
        self.assertEqual(20, response.data['int_field'])

    @ddt.data(
        ('get', [], 200),
        ('post', [{'string_field': 'string_value', 'int_field': 10}], 201),
    )
    @ddt.unpack
    def test_permissions(self, method, args, status_code):
        request = getattr(self.factory, method)('/config/ExampleConfig', *args)

        request.user = User.objects.create_user(
            username='no-perms',
            email='no-perms@example.com',
            password='no-perms',
        )
        response = self.current_view(request)
        self.assertEqual(403, response.status_code)

        request.user = self.user
        response = self.current_view(request)
        self.assertEqual(status_code, response.status_code)
