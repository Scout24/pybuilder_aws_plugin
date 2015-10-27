#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import mock
import tempfile
import boto3
import shutil
import zipfile
from moto import mock_s3
from unittest import TestCase
from pybuilder.core import Project, Logger
from pybuilder_aws_lambda_plugin import upload_zip_to_s3, package_lambda_code


class PackageLambdaCodeTest(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='palp-')
        self.testdir = os.path.join(self.tempdir, 'package_lambda_code_test')
        self.project = Project(basedir=self.testdir, name='palp')
        shutil.copytree('src/unittest/python/package_lambda_code_test/', self.testdir)

        self.project.set_property('dir_target', 'target')
        self.project.set_property('dir_source_main_python', 'src/main/python')
        self.project.set_property('dir_source_main_scripts', 'src/main/scripts')

        self.dir_target = os.path.join(self.testdir, 'target')
        self.zipfile_name = os.path.join(self.dir_target, 'palp.zip')


    def tearDown(self):
        shutil.rmtree(self.tempdir)
        pass

    @mock.patch('pybuilder_aws_lambda_plugin.prepare_dependencies_dir')
    def test_package_lambda_assembles_zipfile_correctly(self,
                                                        prepare_dependencies_dir_mock):
        package_lambda_code(self.project, mock.MagicMock(Logger))
        zf = zipfile.ZipFile(self.zipfile_name)
        expected = sorted(['test_package_directory/__init__.py',
                    'test_module_file.py',
                    'test_script.py'])
        self.assertEqual(sorted(zf.namelist()), expected)


class UploadZipToS3Test(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='palp-')
        self.project = Project(basedir=self.tempdir, name='palp')
        self.project.set_property('dir_target', 'target')
        self.dir_target = os.path.join(self.tempdir, 'target')
        os.mkdir(self.dir_target)
        self.zipfile_name = os.path.join(self.dir_target, 'palp.zip')
        self.test_data = 'testdata'
        with open(self.zipfile_name, 'wb') as fp:
            fp.write(self.test_data)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @mock_s3
    @mock.patch('pybuilder_aws_lambda_plugin.timestamp')
    def test_if_file_was_uploaded_to_s3(self, timestamp_mock):
        timestamp_mock.return_value = '197001010000'
        s3 = boto3.resource('s3')
        s3.create_bucket(Bucket='palp-lambda-zips')

        upload_zip_to_s3(self.project, mock.MagicMock(Logger))

        s3_object = [o for o in s3.Bucket('palp-lambda-zips').objects.all()][0]
        self.assertEqual(s3_object.bucket_name, 'palp-lambda-zips')
        self.assertEqual(s3_object.key, 'palp-197001010000.zip')

    @mock_s3
    @mock.patch('pybuilder_aws_lambda_plugin.timestamp')
    def test_handle_failure_if_no_such_bucket(self, timestamp_mock):
        pass
