#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import mock
import tempfile
import boto3
import shutil
import zipfile
from moto import mock_s3
from unittest import TestCase
from pybuilder.core import Project, Logger
from pybuilder_aws_lambda_plugin import (
    upload_zip_to_s3, package_lambda_code, initialize_plugin)
if sys.version_info[0:2] >= (2, 7):
    from pybuilder_aws_lambda_plugin import upload_json_to_s3


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
    def test_package_lambda_assembles_zipfile_correctly(self,
                                                        prepare_dependencies_dir_mock):
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

    @mock_s3
    def test_handle_failure_if_no_such_bucket(self):
        pass


if sys.version_info[0:2] == (2, 7):
    class UploadJSONToS3(TestCase):

        def setUp(self):
            self.bucket_name = 'palp-cfn-json'
            self.project = Project(basedir=os.path.dirname(__file__),
                                   name='palp', version=123)
            self.test_files = [
                (os.path.join(os.path.dirname(__file__), 'templates'),
                 'alarm-topic.yml'),
                (os.path.join(os.path.dirname(__file__), 'templates'),
                 'ecs-simple-webapp.yml')]
            self.project.set_property('bucket_name', self.bucket_name)
            self.project.set_property('template_key_prefix', 'palp/')
            self.project.set_property(
                'template_file_access_control', 'bucket-owner-full-control')
            self.project.set_property('template_files', self.test_files)

            self.my_mock_s3 = mock_s3()
            self.my_mock_s3.start()
            self.s3 = boto3.resource('s3')
            self.s3.create_bucket(Bucket=self.bucket_name)

        def test_upload_json_fils(self):
            upload_json_to_s3(self.project, mock.MagicMock(Logger))
            s3_object_list = [
                o for o in self.s3.Bucket(self.bucket_name).objects.all()]

            key_prefix = self.project.get_property('template_key_prefix')
            self.assertEqual(s3_object_list[0].bucket_name, self.bucket_name)
            for test_file in self.test_files:
                version_path = '{0}v{1}/{2}'.format(
                    key_prefix, self.project.version,
                    test_file[1].replace('yml', 'json'))
                latest_path = '{0}latest/{1}'.format(
                    key_prefix, test_file[1].replace('yml', 'json'))
                keys = [o.key for o in s3_object_list]
                assert version_path in keys
                assert latest_path in keys

        def tearDown(self):
            self.my_mock_s3.stop()
