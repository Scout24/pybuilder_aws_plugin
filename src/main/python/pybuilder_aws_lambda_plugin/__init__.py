#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pybuilder.core import init
import sys

from .upload_zip_task import upload_zip_to_s3, package_lambda_code
upload_zip_to_s3  # Linting purposes, no other use
package_lambda_code  # Linting purposes, no other use

if sys.version_info[0:2] >= (2, 7):
    from .upload_cfn_task import upload_cfn_to_s3
    upload_cfn_to_s3  # Linting purposes, no other use


@init
def initialize_plugin(project):
    project.set_property(
        'lambda_file_access_control', 'bucket-owner-full-control')
    project.set_property('bucket_prefix', '')

    project.set_property(
        'template_file_access_control', 'bucket-owner-full-control')
    project.set_property('template_key_prefix', '')
    project.set_property('teamcity_parameter', '')
