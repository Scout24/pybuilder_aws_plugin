import os
import subprocess

import zipfile

from pybuilder.core import depends, task
from pybuilder.plugins.python.install_dependencies_plugin import (
    as_pip_argument)

from .helpers import upload_helper, teamcity_helper


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


def prepare_dependencies_dir(project, target_directory, excludes=None):
    """Get all dependencies from project and install them to given dir"""
    excludes = excludes or []
    dependencies = map(lambda dep: as_pip_argument(dep), project.dependencies)
    index_url = project.get_property('install_dependencies_index_url')
    if index_url:
        index_url = "--index-url {0}".format(index_url)
    pip_cmd = 'pip install --target {0} {1} {2}'
    for dependency in dependencies:
        if dependency in excludes:
            continue
        cmd = pip_cmd.format(target_directory, index_url, dependency).split()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout, _ = process.communicate()


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
@depends('package')
def package_lambda_code(project, logger):
    dir_target = project.expand_path('$dir_target')
    lambda_dependencies_dir = os.path.join(dir_target, 'lambda_dependencies')
    excludes = ['boto', 'boto3']
    logger.info('Going to prepare dependencies.')
    prepare_dependencies_dir(
        project, lambda_dependencies_dir, excludes=excludes)
    logger.info('Going to assemble the lambda-zip.')
    path_to_zipfile = get_path_to_zipfile(project)
    archive = zipfile.ZipFile(path_to_zipfile, 'w')
    if os.path.isdir(lambda_dependencies_dir):
        zip_recursive(archive, lambda_dependencies_dir)
    sources = project.expand_path('$dir_source_main_python')
    zip_recursive(archive, sources)
    scripts = project.expand_path('$dir_source_main_scripts')
    zip_recursive(archive, scripts)
    write_version(project, archive)
    archive.close()
    logger.info('Lambda zip is available at: "{0}".'.format(path_to_zipfile))


@task('upload_zip_to_s3', description='Upload a packaged lambda-zip to S3')
@depends('package_lambda_code')
def upload_zip_to_s3(project, logger):
    path_to_zipfile = get_path_to_zipfile(project)
    with open(path_to_zipfile, 'rb') as fp:
        data = fp.read()
    bucket_prefix = project.get_property('bucket_prefix')
    bucket_name = project.get_mandatory_property('bucket_name')
    keyname_version = '{0}v{1}/{2}.zip'.format(
        bucket_prefix, project.version, project.name)
    keyname_latest = '{0}latest/{1}.zip'.format(bucket_prefix, project.name)
    acl = project.get_property('lambda_file_access_control')
    upload_helper(logger, bucket_name, keyname_version, data, acl)
    upload_helper(logger, bucket_name, keyname_latest, data, acl)
    tc_param = project.get_property('teamcity_parameter')
    if project.get_property("teamcity_output") and tc_param:
        teamcity_helper(tc_param, keyname_version)
