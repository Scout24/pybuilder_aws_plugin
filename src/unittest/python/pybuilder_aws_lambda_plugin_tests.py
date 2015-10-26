#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import mock
import tempfile
import boto3
from moto import mock_s3
from unittest import TestCase
from pybuilder.core import Project, Logger
from pybuilder_aws_lambda_plugin import upload_zip_to_s3


class PackageLambdaCodeTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass


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
