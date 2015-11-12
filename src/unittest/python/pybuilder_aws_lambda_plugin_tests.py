#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from unittest import TestCase

import boto3
import mock
from moto import mock_s3
from pybuilder.core import Logger, Project
from pybuilder_aws_lambda_plugin import (
    initialize_plugin, package_lambda_code, prepare_dependencies_dir,
    upload_zip_to_s3)


class TestInitializePlugin(TestCase):

    def test_initialize_sets_variables_correctly(self):
        project = Project('.')
        initialize_plugin(project)
        self.assertEqual(project.get_property('lambda_file_access_control'),
                         'bucket-owner-full-control')
        self.assertEqual(project.get_property('bucket_prefix'),
                         '')
        self.assertEqual(project.get_property('template_file_access_control'),
                         'bucket-owner-full-control')
        self.assertEqual(project.get_property('template_key_prefix'),
                         '')


class PackageLambdaCodeTest(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='palp-')
        self.testdir = os.path.join(self.tempdir, 'package_lambda_code_test')
        self.project = Project(basedir=self.testdir, name='palp')
        shutil.copytree('src/unittest/python/package_lambda_code_test/',
                        self.testdir)

        self.project.set_property('dir_target', 'target')
        self.project.set_property('dir_source_main_python',
                                  'src/main/python')
        self.project.set_property('dir_source_main_scripts',
                                  'src/main/scripts')

        self.dir_target = os.path.join(self.testdir, 'target')
        self.zipfile_name = os.path.join(self.dir_target, 'palp.zip')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @mock.patch('pybuilder_aws_lambda_plugin.prepare_dependencies_dir')
    def test_package_lambda_assembles_zipfile_correctly(
            self, prepare_dependencies_dir_mock):
        package_lambda_code(self.project, mock.MagicMock(Logger))
        zf = zipfile.ZipFile(self.zipfile_name)
        expected = sorted(['test_dependency_module.py',
                           'test_dependency_package/__init__.py',
                           'test_package_directory/__init__.py',
                           'test_module_file.py',
                           'test_script.py'])
        self.assertEqual(sorted(zf.namelist()), expected)


class UploadZipToS3Test(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='palp-')
        self.project = Project(basedir=self.tempdir, name='palp', version=123)
        self.project.set_property('dir_target', 'target')
        self.project.set_property('bucket_name', 'palp-lambda-zips')
        self.project.set_property(
            'lambda_file_access_control', 'bucket-owner-full-control')
        self.project.set_property('bucket_prefix', '')
        self.dir_target = os.path.join(self.tempdir, 'target')
        os.mkdir(self.dir_target)
        self.zipfile_name = os.path.join(self.dir_target, 'palp.zip')
        self.test_data = b'testdata'
        with open(self.zipfile_name, 'wb') as fp:
            fp.write(self.test_data)

        self.my_mock_s3 = mock_s3()
        self.my_mock_s3.start()
        self.s3 = boto3.resource('s3')
        self.s3.create_bucket(Bucket='palp-lambda-zips')

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        self.my_mock_s3.stop()

    def test_if_file_was_uploaded_to_s3(self):

        upload_zip_to_s3(self.project, mock.MagicMock(Logger))

        s3_object_list = [
            o for o in self.s3.Bucket('palp-lambda-zips').objects.all()]
        self.assertEqual(s3_object_list[0].bucket_name, 'palp-lambda-zips')
        self.assertEqual(s3_object_list[0].key, 'latest/palp.zip')
        self.assertEqual(s3_object_list[1].key, 'v123/palp.zip')

    def test_if_file_was_uploaded_to_s3_with_bucket_prefix(self):
        self.project.set_property('bucket_prefix', 'palp/')

        upload_zip_to_s3(self.project, mock.MagicMock(Logger))

        s3_object_list = [
            o for o in self.s3.Bucket('palp-lambda-zips').objects.all()]
        self.assertEqual(s3_object_list[0].bucket_name, 'palp-lambda-zips')
        self.assertEqual(s3_object_list[0].key, 'palp/latest/palp.zip')
        self.assertEqual(s3_object_list[1].key, 'palp/v123/palp.zip')

    @mock.patch("pybuilder_aws_lambda_plugin.flush_text_line")
    def test_teamcity_output_if_set(self, flush_text_line_mock):
        self.project.set_property('teamcity_output', True)

        upload_zip_to_s3(self.project, mock.MagicMock(Logger))

        flush_text_line_mock.assert_called_with("##teamcity[setParameter name='crassus_filename' value='v123/palp.zip']")

    @mock.patch("pybuilder_aws_lambda_plugin.flush_text_line")
    def test_teamcity_output_if_not_set(self, flush_text_line_mock):

        upload_zip_to_s3(self.project, mock.MagicMock(Logger))

        flush_text_line_mock.assert_not_called()


    @mock_s3
    def test_handle_failure_if_no_such_bucket(self):
        pass


class TestPrepareDependenciesDir(TestCase):

    """Testcases for prepare_dependencies_dir()"""

    def setUp(self):
        self.patch_popen = mock.patch(
            'pybuilder_aws_lambda_plugin.subprocess.Popen')
        self.mock_popen = self.patch_popen.start()
        self.patch_aspip = mock.patch(
            'pybuilder_aws_lambda_plugin.as_pip_argument')
        self.mock_aspip = self.patch_aspip.start()
        # Mock return value unmodified
        self.mock_aspip.side_effect = lambda x: x
        self.mock_popen.return_value.communicate.return_value = (1, 2)
        self.input_project = mock.Mock()

    def tearDown(self):
        self.patch_popen.stop()
        self.patch_aspip.stop()

    def test_prepare_dependencies_no_excludes(self):
        """Test prepare_dependencies_dir() w/o excludes."""
        self.input_project.dependencies = ['a', 'b', 'c']
        prepare_dependencies_dir(self.input_project, 'targetdir')
        self.assertEqual(self.mock_aspip.call_count, 3)
        self.assertNotEqual(self.mock_aspip.call_count, 4)
        self.assertEqual(
            list(self.mock_popen.call_args_list), [
                mock.call(
                    ['pip', 'install', '--target', 'targetdir', 'a'],
                    stdout=subprocess.PIPE),
                mock.call(
                    ['pip', 'install', '--target', 'targetdir', 'b'],
                    stdout=subprocess.PIPE),
                mock.call(
                    ['pip', 'install', '--target', 'targetdir', 'c'],
                    stdout=subprocess.PIPE)])
        self.assertEqual(
            self.mock_popen.return_value.communicate.call_count, 3)
        self.assertNotEqual(
            self.mock_popen.return_value.communicate.call_count, 1)

    def test_prepare_dependencies_with_excludes(self):
        """Test prepare_dependencies_dir() w/ excludes."""
        self.input_project.dependencies = ['a', 'b', 'c', 'd', 'e']
        prepare_dependencies_dir(
            self.input_project, 'targetdir', excludes=['b', 'e', 'a'])
        self.assertEqual(self.mock_aspip.call_count, 5)
        self.assertNotEqual(self.mock_aspip.call_count, 4)
        self.assertEqual(
            list(self.mock_popen.call_args_list), [
                mock.call(
                    ['pip', 'install', '--target', 'targetdir', 'c'],
                    stdout=subprocess.PIPE),
                mock.call(
                    ['pip', 'install', '--target', 'targetdir', 'd'],
                    stdout=subprocess.PIPE)])
        self.assertEqual(
            self.mock_popen.return_value.communicate.call_count, 2)
        self.assertNotEqual(
            self.mock_popen.return_value.communicate.call_count, 1)


if sys.version_info[0:2] == (2, 7):
    from version_specific import UploadJSONToS3
    UploadJSONToS3  # Linting purposes, no other use
