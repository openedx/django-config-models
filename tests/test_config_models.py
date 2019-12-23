"""
Tests of ConfigurationModel
"""
from __future__ import unicode_literals, absolute_import

import ddt
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import six
from rest_framework.test import APIRequestFactory

from freezegun import freeze_time

from mock import patch, Mock

from config_models.views import ConfigurationModelCurrentAPIView
from example.models import ExampleConfig, ExampleKeyedConfig, ManyToManyExampleConfig


@patch('config_models.models.cache')
class ConfigurationModelTests(TestCase):
    """
    Tests of ConfigurationModel
    """
    def setUp(self):
        super(ConfigurationModelTests, self).setUp()
        self.user = User()
        self.user.save()

    def test_cache_deleted_on_save(self, mock_cache):
        ExampleConfig(changed_by=self.user).save()
        mock_cache.delete.assert_called_with(ExampleConfig.cache_key_name())

    def test_cache_key_name(self, __):
        self.assertEqual(ExampleConfig.cache_key_name(), 'configuration/ExampleConfig/current')

    def test_no_config_empty_cache(self, mock_cache):
        mock_cache.get.return_value = None

        current = ExampleConfig.current()
        self.assertEqual(current.int_field, 10)
        self.assertEqual(current.string_field, '')
        mock_cache.set.assert_called_with(ExampleConfig.cache_key_name(), current, 300)

    def test_no_config_full_cache(self, mock_cache):
        current = ExampleConfig.current()
        self.assertEqual(current, mock_cache.get.return_value)

    def test_config_ordering(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            first = ExampleConfig(changed_by=self.user)
            first.string_field = 'first'
            first.save()

        second = ExampleConfig(changed_by=self.user)
        second.string_field = 'second'
        second.save()

        self.assertEqual(ExampleConfig.current().string_field, 'second')

    def test_cache_set(self, mock_cache):
        mock_cache.get.return_value = None

        first = ExampleConfig(changed_by=self.user)
        first.string_field = 'first'
        first.save()

        ExampleConfig.current()

        mock_cache.set.assert_called_with(ExampleConfig.cache_key_name(), first, 300)

    def test_active_annotation(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleConfig.objects.create(string_field='first')

        ExampleConfig.objects.create(string_field='second')

        rows = ExampleConfig.objects.with_active_flag().order_by('-change_date')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].string_field, 'second')
        self.assertEqual(rows[0].is_active, True)
        self.assertEqual(rows[1].string_field, 'first')
        self.assertEqual(rows[1].is_active, False)

    def test_keyed_active_annotation(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig.objects.create(left='left', right='right', user=self.user, string_field='first')

        ExampleKeyedConfig.objects.create(left='left', right='right', user=self.user, string_field='second')

        rows = ExampleKeyedConfig.objects.with_active_flag().order_by('-change_date')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].string_field, 'second')
        self.assertEqual(rows[0].is_active, True)
        self.assertEqual(rows[1].string_field, 'first')
        self.assertEqual(rows[1].is_active, False)

    def test_always_insert(self, __):
        config = ExampleConfig(changed_by=self.user, string_field='first')
        config.save()
        config.string_field = 'second'
        config.save()

        self.assertEqual(2, ExampleConfig.objects.all().count())

    def test_equality(self, mock_cache):
        mock_cache.get.return_value = None

        config = ExampleConfig(changed_by=self.user, string_field='first')
        config.save()

        self.assertTrue(ExampleConfig.equal_to_current({"string_field": "first"}))
        self.assertTrue(ExampleConfig.equal_to_current({"string_field": "first", "enabled": False}))
        self.assertTrue(ExampleConfig.equal_to_current({"string_field": "first", "int_field": 10}))

        self.assertFalse(ExampleConfig.equal_to_current({"string_field": "first", "enabled": True}))
        self.assertFalse(ExampleConfig.equal_to_current({"string_field": "first", "int_field": 20}))
        self.assertFalse(ExampleConfig.equal_to_current({"string_field": "second"}))

        self.assertFalse(ExampleConfig.equal_to_current({}))

    def test_equality_custom_fields_to_ignore(self, mock_cache):
        mock_cache.get.return_value = None

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

    def test_equality_ignores_many_to_many(self, mock_cache):
        mock_cache.get.return_value = None
        config = ManyToManyExampleConfig(changed_by=self.user, string_field='first')
        config.save()

        second_user = User(username="second_user")
        second_user.save()
        config.many_user_field.add(second_user)  # pylint: disable=no-member
        config.save()

        # The many-to-many field is ignored in comparison.
        self.assertTrue(
            ManyToManyExampleConfig.equal_to_current({"string_field": "first", "many_user_field": "removed"})
        )


@ddt.ddt
@patch('config_models.models.cache')
class KeyedConfigurationModelTests(TestCase):
    """
    Tests for ``ConfigurationModels`` with keyed configuration.
    """
    def setUp(self):
        super(KeyedConfigurationModelTests, self).setUp()
        self.user = User()
        self.user.save()

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_cache_key_name(self, left, right, _mock_cache):
        self.assertEqual(
            ExampleKeyedConfig.cache_key_name(left, right, self.user),
            'configuration/ExampleKeyedConfig/current/{},{},{}'.format(left, right, self.user)
        )

    @ddt.data(
        ((), 'left,right,user'),
        (('left', 'right'), 'left,right'),
        (('left', ), 'left')
    )
    @ddt.unpack
    def test_key_values_cache_key_name(self, args, expected_key, _mock_cache):
        self.assertEqual(
            ExampleKeyedConfig.key_values_cache_key_name(*args),
            'configuration/ExampleKeyedConfig/key_values/{}'.format(expected_key))

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_no_config_empty_cache(self, left, right, mock_cache):
        mock_cache.get.return_value = None

        current = ExampleKeyedConfig.current(left, right, self.user)
        self.assertEqual(current.int_field, 10)
        self.assertEqual(current.string_field, '')
        mock_cache.set.assert_called_with(ExampleKeyedConfig.cache_key_name(left, right, self.user), current, 300)

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_no_config_full_cache(self, left, right, mock_cache):
        current = ExampleKeyedConfig.current(left, right, self.user)
        self.assertEqual(current, mock_cache.get.return_value)

    def test_config_ordering(self, mock_cache):
        mock_cache.get.return_value = None

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

    def test_cache_set(self, mock_cache):
        mock_cache.get.return_value = None

        first = ExampleKeyedConfig(
            changed_by=self.user,
            left='left',
            right='right',
            user=self.user,
            string_field='first',
        )
        first.save()

        ExampleKeyedConfig.current('left', 'right', self.user)

        mock_cache.set.assert_called_with(ExampleKeyedConfig.cache_key_name('left', 'right', self.user), first, 300)

    def test_key_values(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(left='left_a', right='right_a', user=self.user, changed_by=self.user).save()
            ExampleKeyedConfig(left='left_b', right='right_b', user=self.user, changed_by=self.user).save()

        ExampleKeyedConfig(left='left_a', right='right_a', user=self.user, changed_by=self.user).save()
        ExampleKeyedConfig(left='left_b', right='right_b', user=self.user, changed_by=self.user).save()

        unique_key_pairs = ExampleKeyedConfig.key_values()
        self.assertEqual(len(unique_key_pairs), 2)
        self.assertEqual(
            set(unique_key_pairs),
            set([('left_a', 'right_a', self.user.id), ('left_b', 'right_b', self.user.id)])
        )
        unique_left_keys = ExampleKeyedConfig.key_values('left', flat=True)
        self.assertEqual(len(unique_left_keys), 2)
        self.assertEqual(set(unique_left_keys), set(['left_a', 'left_b']))

    def test_key_string_values(self, mock_cache):
        """ Ensure str() vs unicode() doesn't cause duplicate cache entries """
        ExampleKeyedConfig(
            left='left',
            right=u'\N{RIGHT ANGLE BRACKET}\N{SNOWMAN}',
            enabled=True,
            int_field=10,
            user=self.user,
            changed_by=self.user
        ).save()
        mock_cache.get.return_value = None

        entry = ExampleKeyedConfig.current('left', u'\N{RIGHT ANGLE BRACKET}\N{SNOWMAN}', self.user)
        key = mock_cache.get.call_args[0][0]
        self.assertEqual(entry.int_field, 10)
        mock_cache.get.assert_called_with(key)
        self.assertEqual(mock_cache.set.call_args[0][0], key)

        mock_cache.get.reset_mock()
        entry = ExampleKeyedConfig.current(u'left', u'\N{RIGHT ANGLE BRACKET}\N{SNOWMAN}', self.user)
        self.assertEqual(entry.int_field, 10)
        mock_cache.get.assert_called_with(key)

    def test_current_set(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(left='left_a', right='right_a', int_field=0, user=self.user, changed_by=self.user).save()
            ExampleKeyedConfig(left='left_b', right='right_b', int_field=0, user=self.user, changed_by=self.user).save()

        ExampleKeyedConfig(left='left_a', right='right_a', int_field=1, user=self.user, changed_by=self.user).save()
        ExampleKeyedConfig(left='left_b', right='right_b', int_field=2, user=self.user, changed_by=self.user).save()

        queryset = ExampleKeyedConfig.objects.current_set()
        self.assertEqual(len(queryset.all()), 2)
        self.assertEqual(
            set(queryset.order_by('int_field').values_list('int_field', flat=True)),
            set([1, 2])
        )

    def test_active_annotation(self, mock_cache):
        mock_cache.get.return_value = None

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

    def test_key_values_cache(self, mock_cache):
        mock_cache.get.return_value = None
        self.assertEqual(ExampleKeyedConfig.key_values(), [])
        mock_cache.set.assert_called_with(ExampleKeyedConfig.key_values_cache_key_name(), [], 300)

        fake_result = [('a', 'b'), ('c', 'd')]
        mock_cache.get.return_value = fake_result
        self.assertEqual(ExampleKeyedConfig.key_values(), fake_result)

    def test_equality(self, mock_cache):
        mock_cache.get.return_value = None

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
class ConfigurationModelAPITests(TestCase):
    """
    Tests for the configuration model API.
    """
    def setUp(self):
        super(ConfigurationModelAPITests, self).setUp()
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@example.com',
            password='test_pass',
        )
        self.user.is_superuser = True
        self.user.save()

        self.current_view = ConfigurationModelCurrentAPIView.as_view(model=ExampleConfig)

        # Disable caching while testing the API
        patcher = patch('config_models.models.cache', Mock(get=Mock(return_value=None)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_insert(self):
        self.assertEqual("", ExampleConfig.current().string_field)

        request = self.factory.post('/config/ExampleConfig', {"string_field": "string_value"})
        request.user = self.user
        __ = self.current_view(request)

        self.assertEqual("string_value", ExampleConfig.current().string_field)
        self.assertEqual(self.user, ExampleConfig.current().changed_by)

    def test_multiple_inserts(self):
        for i in six.moves.range(3):  # pylint: disable=no-member
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
