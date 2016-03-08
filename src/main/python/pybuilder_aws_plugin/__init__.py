#!/usr/bin/env python
# -*- coding: utf-8 -*-
# flake8: noqa

import sys

from pybuilder.core import init, task, depends

from .lambda_tasks import upload_zip_to_s3, package_lambda_code, lambda_release

if sys.version_info[0:2] >= (2, 7):
    # cfn-sphere needs Python 2.7, skip cfn handling for older Python versions
    from .cfn_tasks import upload_cfn_to_s3, cfn_release

    @task(description='Release on S3 by copying everything to latest')
    @depends('lambda_release',
             'cfn_release')
    def release_custom_resource():
        pass

    @task(description='Upload lambda and cfn results to S3')
    @depends('package_lambda_code',
             'upload_zip_to_s3',
             'upload_cfn_to_s3')
    def upload_custom_resource():
        pass

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
