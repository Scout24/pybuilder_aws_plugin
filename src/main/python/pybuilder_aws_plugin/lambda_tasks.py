#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import zipfile

from pybuilder.core import depends, task

from .helpers import (upload_helper,
                      copy_helper,
                      teamcity_helper,
                      check_acl_parameter_validity,
                      )


def zip_recursive(archive, directory, folder=''):
    """Zip directories recursively"""
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            archive.write(
                    os.path.join(directory, item), os.path.join(folder, item),
                    zipfile.ZIP_DEFLATED)
        elif os.path.isdir(os.path.join(directory, item)):
            zip_recursive(
                    archive, os.path.join(directory, item),
                    folder=os.path.join(folder, item))


def as_pip_argument(dependency):
    return "{0}{1}".format(dependency.name, dependency.version or "")


def prepare_dependencies_dir(logger, project, target_directory, excludes=None):
    """Get all dependencies from project and install them to given dir"""
    excludes = excludes or []
    dependencies = map(lambda dep: as_pip_argument(dep), project.dependencies)

    index_url = project.get_property('install_dependencies_index_url')
    if index_url:
        index_url = "--index-url {0}".format(index_url)
    else:
        index_url = ""

    pip_cmd = 'pip install --target {0} {1} {2}'
    for dependency in dependencies:
        if dependency in excludes:
            logger.debug("Not installing dependency {0}.".format(dependency))
            continue

        cmd = pip_cmd.format(target_directory, index_url, dependency)
        logger.debug("Installing dependency {0}: '{1}'".format(dependency, cmd))

        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        process.communicate()
        if process.returncode != 0:
            msg = "Command '{0}' failed to install dependency: {1}".format(
                    cmd, process.returncode)
            raise Exception(msg)


def get_path_to_zipfile(project):
    return os.path.join(
            project.expand_path('$dir_target'), '{0}.zip'.format(project.name))


def write_version(project, archive):
    """Get the current version and write it to a version file"""
    filename = os.path.join(project.expand_path('$dir_target'), 'VERSION')
    with open(filename, 'w') as version_file:
        version_file.write(project.version)
    archive.write(filename, 'VERSION')


@task('package_lambda_code',
      description='Package the modules, dependencies and scripts into a '
                  'lambda-zip')
@depends('clean',
         'install_build_dependencies',
         'publish',
         'package')
def package_lambda_code(project, logger):
    dir_target = project.expand_path('$dir_target')
    lambda_dependencies_dir = os.path.join(dir_target, 'lambda_dependencies')
    excludes = ['boto', 'boto3']
    logger.info('Going to prepare dependencies.')
    prepare_dependencies_dir(
            logger, project, lambda_dependencies_dir, excludes=excludes)
    logger.info('Going to assemble the lambda-zip.')
    path_to_zipfile = get_path_to_zipfile(project)
    archive = zipfile.ZipFile(path_to_zipfile, 'w')
    if os.path.isdir(lambda_dependencies_dir):
        zip_recursive(archive, lambda_dependencies_dir)
    sources = project.expand_path('$dir_source_main_python')
    zip_recursive(archive, sources)
    scripts = project.expand_path('$dir_source_main_scripts')
    if os.path.exists(scripts) and os.path.isdir(scripts):
        zip_recursive(archive, scripts)
    write_version(project, archive)
    archive.close()
    logger.info('Lambda-zip is available at: "{0}".'.format(path_to_zipfile))


@task('upload_zip_to_s3', description='Upload a packaged lambda-zip to S3')
@depends('package_lambda_code')
def upload_zip_to_s3(project, logger):
    path_to_zipfile = get_path_to_zipfile(project)
    logger.info('Found lambda-zip at: "{0}".'.format(path_to_zipfile))
    with open(path_to_zipfile, 'rb') as fp:
        data = fp.read()
    bucket_prefix = project.get_property('bucket_prefix')
    bucket_name = project.get_mandatory_property('bucket_name')
    keyname_version = '{0}v{1}/{2}.zip'.format(
            bucket_prefix, project.version, project.name)
    acl = project.get_property('lambda_file_access_control')
    check_acl_parameter_validity('lambda_file_access_control', acl)
    upload_helper(logger, bucket_name, keyname_version, data, acl)
    tc_param = project.get_property('teamcity_parameter')
    if project.get_property("teamcity_output") and tc_param:
        teamcity_helper(tc_param, keyname_version)

@task('lambda_release', description='Copy lambda zip file from versioned path to latest path in S3')
def lambda_release(project,logger):
    bucket_prefix = project.get_property('bucket_prefix')
    bucket_name = project.get_mandatory_property('bucket_name')
    acl = project.get_property('lambda_file_access_control')
    check_acl_parameter_validity('lambda_file_access_control', acl)

    source_key = '{0}v{1}/{2}.zip'.format(bucket_prefix, project.version, project.name)
    destination_key = '{0}latest/{1}.zip'.format(bucket_prefix, project.name)
    copy_helper(logger, bucket_name, source_key, destination_key, acl)

