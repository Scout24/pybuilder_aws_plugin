#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pybuilder.core import task

from .helpers import upload_helper, copy_helper, check_acl_parameter_validity


@task('upload_cfn_to_s3',
      description='Convert & upload CloudFormation templates in JSON '
                  'created out of the CFN-Sphere template YAML files')
def upload_cfn_to_s3(project, logger):
    """
    This task is separate since they only work with Python2 >2.6 by
    the time being. Python3 support is underway.

    This means, when using Python<2.7, this task is not visible
    (see __init__.py).
    """
    from cfn_sphere.file_loader import FileLoader
    from cfn_sphere.template.transformer import CloudFormationTemplateTransformer

    for path, filename in project.get_property('template_files'):
        template = FileLoader.get_cloudformation_template(filename, path)
        transformed = CloudFormationTemplateTransformer.transform_template(
                template)
        output = transformed.get_template_json()

        bucket_name = project.get_property('bucket_name')
        key_prefix = project.get_property('template_key_prefix')
        filename = filename.replace('.yml', '.json')
        filename = filename.replace('.yaml', '.json')
        version_path = '{0}v{1}/{2}'.format(
                key_prefix, project.version, filename)
        # latest_path = '{0}latest/{1}'.format(key_prefix, filename)

        acl = project.get_property('template_file_access_control')
        check_acl_parameter_validity('template_file_access_control', acl)
        upload_helper(logger, bucket_name, version_path, output, acl)
        # upload_helper(logger, bucket_name, latest_path, output, acl)

@task('cfn_release', description='Copy CFN templates from versioned path to latest path in S3')
def cfn_release(project, logger):
    bucket_name = project.get_property('bucket_name')
    key_prefix = project.get_property('template_key_prefix')
    acl = project.get_property('template_file_access_control')
    check_acl_parameter_validity('template_file_access_control', acl)

    for path, filename in project.get_property('template_files'):
        filename = filename.replace('.yml', '.json').replace('.yaml', '.json')
        source_key = '{0}v{1}/{2}'.format(key_prefix, project.version, filename)
        destination_key = '{0}latest/{1}'.format(key_prefix, filename)
        copy_helper(logger, bucket_name, source_key, destination_key, acl)
