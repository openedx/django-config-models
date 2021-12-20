"""
Django Model baseclass for database-backed configuration.
"""


from django.conf import settings
# The following import exists for backwards compatibility (because a number of
# library users assume config_models.models.cache is importable), but
# ConfigModels will now ignore the custom 'configuration' cache setting and just
# use TieredCache, which will make use of a local request cache + the default
# Django cache.
from django.core.cache import cache  # pylint: disable=unused-import
from django.db import models
from django.utils.translation import gettext_lazy as _
from edx_django_utils.cache.utils import TieredCache
from rest_framework.utils import model_meta


class ConfigurationModelManager(models.Manager):
    """
    Query manager for ConfigurationModel
    """
    def _current_ids_subquery(self):
        """
        Internal helper method to return an SQL string that will get the IDs of
        all the current entries (i.e. the most recent entry for each unique set
        of key values). Only useful if KEY_FIELDS is set.
        """
        return self.values(*self.model.KEY_FIELDS).annotate(max=models.Max('pk')).values('max')

    def current_set(self):
        """
        A queryset for the active configuration entries only. Only useful if KEY_FIELDS is set.

        Active means the means recent entries for each unique combination of keys. It does not
        necessaryily mean enbled.
        """
        assert self.model.KEY_FIELDS != (), "Just use model.current() if there are no KEY_FIELDS"
        return self.get_queryset().filter(
            pk__in=self._current_ids_subquery()
        ).annotate(
            is_active=models.Value(1, output_field=models.IntegerField())
        )

    def with_active_flag(self):
        """
        A query set where each result is annotated with an 'is_active' field that indicates
        if it's the most recent entry for that combination of keys.
        """
        if self.model.KEY_FIELDS:
            return self.get_queryset().annotate(
                is_active=models.ExpressionWrapper(
                    models.Q(pk__in=self._current_ids_subquery()),
                    output_field=models.IntegerField(),
                )
            )
        return self.get_queryset().annotate(
            is_active=models.ExpressionWrapper(
                models.Q(pk=self.model.current().pk),
                output_field=models.IntegerField(),
            )
        )


class ConfigurationModel(models.Model):
    """
    Abstract base class for model-based configuration

    Properties:
        cache_timeout (int): The number of seconds that this configuration
            should be cached
    """

    class Meta:
        abstract = True
        ordering = ("-change_date", )

    objects = ConfigurationModelManager()

    KEY_FIELDS = ()

    # The number of seconds
    cache_timeout = 600

    change_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Change date"))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        editable=False,
        null=True,
        on_delete=models.PROTECT,
        # Translators: this label indicates the name of the user who made this change:
        verbose_name=_("Changed by"),
    )
    enabled = models.BooleanField(default=False, verbose_name=_("Enabled"))

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Clear the cached value when saving a new configuration entry
        """
        # Always create a new entry, instead of updating an existing model
        self.pk = None  # pylint: disable=invalid-name
        super().save(
            force_insert,
            force_update,
            using,
            update_fields
        )
        TieredCache.delete_all_tiers(self.cache_key_name(*[getattr(self, key) for key in self.KEY_FIELDS]))
        if self.KEY_FIELDS:
            TieredCache.delete_all_tiers(self.key_values_cache_key_name())

    @classmethod
    def cache_key_name(cls, *args):
        """Return the name of the key to use to cache the current configuration"""
        if cls.KEY_FIELDS != ():    # pylint: disable=use-implicit-booleaness-not-comparison
            if len(args) != len(cls.KEY_FIELDS):
                raise TypeError(
                    f"cache_key_name() takes exactly {len(cls.KEY_FIELDS)} arguments ({len(args)} given)"
                )
            return f"configuration/{cls.__name__}/current/{','.join(str(arg) for arg in args)}"
        else:
            return f'configuration/{cls.__name__}/current'

    @classmethod
    def current(cls, *args):
        """
        Return the active configuration entry, either from cache,
        from the database, or by creating a new empty entry (which is not
        persisted).
        """
        cache_key = cls.cache_key_name(*args)
        cached_response = TieredCache.get_cached_response(cache_key)
        if cached_response.is_found:
            return cached_response.value

        key_dict = dict(zip(cls.KEY_FIELDS, args))
        try:
            current = cls.objects.filter(**key_dict).order_by('-change_date')[0]
        except IndexError:
            current = cls(**key_dict)

        TieredCache.set_all_tiers(cache_key, current, cls.cache_timeout)
        return current

    @classmethod
    def is_enabled(cls, *key_fields):
        """
        Returns True if this feature is configured as enabled, else False.

        Arguments:
            key_fields: The positional arguments are the KEY_FIELDS used to identify the
                configuration to be checked.
        """
        return cls.current(*key_fields).enabled

    @classmethod
    def key_values_cache_key_name(cls, *key_fields):
        """ Key for fetching unique key values from the cache """
        key_fields = key_fields or cls.KEY_FIELDS
        return f"configuration/{cls.__name__}/key_values/{','.join(key_fields)}"

    @classmethod
    def key_values(cls, *key_fields, **kwargs):
        """
        Get the set of unique values in the configuration table for the given
        key[s]. Calling cls.current(*value) for each value in the resulting
        list should always produce an entry, though any such entry may have
        enabled=False.

        Arguments:
            key_fields: The positional arguments are the KEY_FIELDS to return. For example if
                you had a course embargo configuration where each entry was keyed on (country,
                course), then you might want to know "What countries have embargoes configured?"
                with cls.key_values('country'), or "Which courses have country restrictions?"
                with cls.key_values('course'). You can also leave this unspecified for the
                default, which returns the distinct combinations of all keys.
            flat: If you pass flat=True as a kwarg, it has the same effect as in Django's
                'values_list' method: Instead of returning a list of lists, you'll get one list
                of values. This makes sense to use whenever there is only one key being queried.

        Return value:
            List of lists of each combination of keys found in the database.
            e.g. [("Italy", "course-v1:SomeX+some+2015"), ...] for the course embargo example
        """
        flat = kwargs.pop('flat', False)
        assert not kwargs, "'flat' is the only kwarg accepted"
        key_fields = key_fields or cls.KEY_FIELDS
        cache_key = cls.key_values_cache_key_name(*key_fields)
        cached_response = TieredCache.get_cached_response(cache_key)
        if cached_response.is_found:
            return cached_response.value

        values = list(cls.objects.values_list(*key_fields, flat=flat).order_by().distinct())
        TieredCache.set_all_tiers(cache_key, values, cls.cache_timeout)
        return values

    def fields_equal(self, instance, fields_to_ignore=("id", "change_date", "changed_by")):
        """
        Compares this instance's fields to the supplied instance to test for equality.
        This will ignore any fields in `fields_to_ignore`.

        Note that this method ignores many-to-many fields.

        Args:
            instance: the model instance to compare
            fields_to_ignore: List of fields that should not be compared for equality. By default
            includes `id`, `change_date`, and `changed_by`.

        Returns: True if the checked fields are all equivalent, else False
        """
        for field in self._meta.get_fields():
            if not field.many_to_many and field.name not in fields_to_ignore:
                if getattr(instance, field.name) != getattr(self, field.name):
                    return False

        return True

    @classmethod
    def equal_to_current(cls, json, fields_to_ignore=("id", "change_date", "changed_by")):
        """
        Compares for equality this instance to a model instance constructed from the supplied JSON.
        This will ignore any fields in `fields_to_ignore`.

        Note that this method cannot handle fields with many-to-many associations, as those can only
        be set on a saved model instance (and saving the model instance will create a new entry).
        All many-to-many field entries will be removed before the equality comparison is done.

        Args:
            json: json representing an entry to compare
            fields_to_ignore: List of fields that should not be compared for equality. By default
            includes `id`, `change_date`, and `changed_by`.

        Returns: True if the checked fields are all equivalent, else False
        """

        # Remove many-to-many relationships from json.
        # They require an instance to be already saved.
        info = model_meta.get_field_info(cls)
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in json):
                json.pop(field_name)

        new_instance = cls(**json)
        key_field_args = tuple(getattr(new_instance, key) for key in cls.KEY_FIELDS)
        current = cls.current(*key_field_args)
        # If current.id is None, no entry actually existed and the "current" method created it.
        if current.id is not None:
            return current.fields_equal(new_instance, fields_to_ignore)

        return False
