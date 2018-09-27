"""
Gets waffle data from current environment and outputs it to a file
"""
from __future__ import absolute_import, print_function, unicode_literals

import io
import json
import six

from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder


class Command(BaseCommand):
    """
    This command will produce a report detailing the current state of all
    waffle toggles (flags, switches and samples) configured in the IDA in which
    it is installed.
    """

    help = """
    Gathers current waffle feature toggle configuration and writes it to file
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--file',
            dest='file',
            default='waffle_configuration.json',
            help='Text file for writing waffle configuration report'
        )

    def handle(self, *args, **options):
        output_file_path = options['file']

        waffle_configurations = {}

        for toggle_type in ['waffle.flag', 'waffle.switch', 'waffle.sample']:
            print("Querying db for all instances of {}".format(toggle_type))
            toggle_configuration = self._get_toggle_configurations(toggle_type)
            print(
                "Discovered {} instances of {} in the db".format(
                    len(toggle_configuration), toggle_type
                )
            )
            waffle_configurations[toggle_type] = toggle_configuration

        with io.open(output_file_path, 'w', encoding="utf-8") as outfile:
            report_json = six.text_type(
                json.dumps(
                    waffle_configurations,
                    indent=4,
                    cls=DjangoJSONEncoder,
                    sort_keys=True
                )
            )
            outfile.write(report_json)

        print(
            "Waffle configuration report successfully written to {}".format(
                output_file_path
            )
        )

    def _get_toggle_configurations(self, toggle_type):
        """
        given a type of feature toggle (waffle), query the database for all
        instances of that model and return a dictionary, mapping the name of
        each instance to its attributes
        """
        toggle_configurations = {}
        model = apps.get_model(toggle_type)
        instances = list(model.objects.values())
        for instance in instances:
            instance_name = instance['name']
            toggle_configurations[instance_name] = instance
        return toggle_configurations
