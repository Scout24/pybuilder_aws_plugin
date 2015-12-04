#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa

import sys

from pybuilder.core import init

from .lambda_tasks import upload_zip_to_s3, package_lambda_code

if sys.version_info[0:2] >= (2, 7):
    from .cfn_tasks import upload_cfn_to_s3


@init
def initialize_plugin(project):
    """ Setup plugin defaults. """
    project.set_property(
        'lambda_file_access_control', 'bucket-owner-full-control')
    project.set_property('bucket_prefix', '')

    project.set_property(
        'template_file_access_control', 'bucket-owner-full-control')
    project.set_property('template_key_prefix', '')
    project.set_property('teamcity_parameter', '')
