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
from rest_framework.renderers import JSONRenderer

from config_models.models import ConfigurationModel
from config_models.utils import get_serializer_class

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
        config_model_list = ConfigurationModel.__subclasses__()
        if len(config_model_list) > 0:
            waffle_details['config_models'] = {}
            for config_model in config_model_list:
                model_data = {}
                config_model_name = config_model.__name__
                if config_model.KEY_FIELDS:
                    try:
                        config_key_values = config_model.key_values()
                        for key_value in config_key_values:
                            print key_value
                    except:
                        print "Ahh abstract model!"
                else:
                    current_config_model = config_model.current()
                    serializer_class = get_serializer_class(config_model)
                    serializer = serializer_class(current_config_model)
                    model_data = serializer.data
                    
                waffle_details['config_models'][config_model_name] = model_data;

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

        waffle_sample_model = apps.get_model('waffle.sample')
        waffle_sample_list = waffle_sample_model.objects.values()
        if len(waffle_sample_list) > 0:
            waffle_details['waffle_samples'] = {}
            for waffle_sample in waffle_sample_list:
                waffle_sample_name = waffle_sample['name']
                waffle_details['waffle_samples'][waffle_sample_name] = waffle_sample;

        with open(output_file_path, 'w') as outfile:
            json.dump(waffle_details, outfile, indent=4, cls=DjangoJSONEncoder, sort_keys=True)

        outfile.close()
        print "Output written!"
