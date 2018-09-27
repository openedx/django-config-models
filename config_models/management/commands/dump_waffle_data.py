"""
Gets waffle data from current environment and outputs it to a file
"""
from __future__ import unicode_literals, absolute_import

import os
import io
import json
import pprint

from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder

class Command(BaseCommand):
    """
    This command will return waffle data into an output file
    that can be specified or to the default.
    """
    help = """
    Gets Waffle ConfigurationModel data and outputs it to a file

        $ ... dump_waffle_data
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--file',
            dest='file',
            default=False,
            help='Text file to export Waffle ConfigurationModel data'
        )

    def handle(self, *args, **options):
        output_file_path = 'waffle_data_output.json'
        if 'file' in options and options['file']:
            output_file_path = options['file']

        waffle_details = {}

        # TODO - cleanup duplicatation
        # / make a list of models to check and loop through that instead
        waffle_flag_model = apps.get_model('waffle.flag')
        waffle_flag_list = waffle_flag_model.objects.values()
        if len(waffle_flag_list) > 0:
            waffle_details['waffle_flags'] = {}
            for waffle_flag in waffle_flag_list:
                waffle_flag_name = waffle_flag['name']
                waffle_details['waffle_flags'][waffle_flag_name] = waffle_flag;

        waffle_switch_model = apps.get_model('waffle.switch')
        waffle_switch_list = waffle_switch_model.objects.values()
        if len(waffle_switch_list) > 0:
            waffle_details['waffle_switches'] = {}
            for waffle_switch in waffle_switch_list:
                waffle_switch_name = waffle_switch['name']
                waffle_details['waffle_switches'][waffle_switch_name] = waffle_switch;

        # waffle samples?
        # waffle.sample
        # waffle course overrides?
        # openedx.core.djangoapps.waffle_utils.waffleflagcourseoverridemodel ? 
        # 'openedx.core.djangoapps.waffle_utils.models.WaffleFlagCourseOverrideModel'

        with io.open(output_file_path, 'w') as outfile:
            outfile.write(unicode(json.dumps(waffle_details, cls=DjangoJSONEncoder)))

        outfile.close()
        pprint.pprint(waffle_details)
