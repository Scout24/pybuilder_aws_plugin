#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import boto3
import zipfile
import subprocess

from pybuilder.core import description, task, depends, init
import datetime
from pybuilder.plugins.python.install_dependencies_plugin import as_pip_argument


def zip_recursive(archive, directory, folder=""):
    """Zip directories recursively"""
    for item in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, item)):
            archive.write(os.path.join(directory, item),
                          os.path.join(folder, item),
                          zipfile.ZIP_DEFLATED)
        elif os.path.isdir(os.path.join(directory, item)):
            zip_recursive(archive,
                          os.path.join(directory, item),
                          folder=os.path.join(folder, item))


def prepare_dependencies_dir(project, target_directory, excludes=None):  # pragma: nocover
    """Get all dependencies from project and install them to given dir"""
    excludes = excludes or []
    dependencies = map(lambda dep: as_pip_argument(dep), project.dependencies)
    pip_cmd = 'pip install --target {0} {1}'
    for dependency in dependencies:
        if dependency in excludes:
            continue
        cmd = pip_cmd.format(target_directory, dependency).split()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout, _ = process.communicate()


def get_path_to_zipfile(project):
    return os.path.join(project.expand_path("$dir_target"),
                        "{0}.zip".format(project.name))


def timestamp():
    return datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')


@task
@description("Package the modules, dependencies and scripts into a lambda-zip")
@depends('package')
def package_lambda_code(project, logger):
    dir_target = project.expand_path("$dir_target")
    lambda_dependencies_dir = os.path.join(dir_target, "lambda_dependencies")
    excludes = ['boto', 'boto3']
    logger.info("Going to prepare dependencies.")
    prepare_dependencies_dir(project,
                             lambda_dependencies_dir,
                             excludes=excludes)
    logger.info("Going to assemble the lambda-zip.")
    path_to_zipfile = get_path_to_zipfile(project)
    archive = zipfile.ZipFile(path_to_zipfile, 'w')
    if os.path.isdir(lambda_dependencies_dir):
        zip_recursive(archive, lambda_dependencies_dir)
    sources = project.expand_path("$dir_source_main_python")
    zip_recursive(archive, sources)
    scripts = project.expand_path("$dir_source_main_scripts")
    zip_recursive(archive, scripts)
    archive.close()
    logger.info("Lambda zip is available at: '{0}'.".format(path_to_zipfile))


@init
def initialize_upload_zip_to_s3(project):
    project.set_property('lambda_file_access_control',
                         'bucket-owner-full-control')


@task
@description("Upload a packaged lambda-zip to S3")
@depends('package_lambda_code')
def upload_zip_to_s3(project, logger):
    path_to_zipfile = get_path_to_zipfile(project)
    with open(path_to_zipfile, 'rb') as fp:
        data = fp.read()
    keyname = '{0}-{1}.zip'.format(project.name, timestamp())
    bucket_name = project.get_mandatory_property("bucket_name")
    s3 = boto3.resource('s3')
    logger.info("Uploading lambda-zip to bucket: '{0}' as key: '{1}'".
                format(bucket_name, keyname))
    acl = project.get_property('lambda_file_access_control')
    s3.Bucket(bucket_name).put_object(Key=keyname,
                                      Body=data,
                                      ACL=acl)
