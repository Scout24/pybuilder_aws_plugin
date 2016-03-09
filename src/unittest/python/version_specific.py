"""
These tests are separate since they only work with Python2 >2.6 by
the time being. Python3 support is underway.
"""

import os
import mock
from unittest import TestCase

import boto3
from moto import mock_s3
from pybuilder.core import Logger, Project
from pybuilder.errors import BuildFailedException

from pybuilder_aws_plugin import upload_cfn_to_s3, cfn_release


class TestsWithS3(TestCase):
    def setUp(self):
        self.bucket_name = 'palp-cfn-json'
        basedir = os.path.dirname(__file__)
        self.project = Project(basedir=basedir,
                               name='palp', version='123')
        self.test_files = [
            (os.path.join(basedir, 'templates'),'alarm-topic.yml'),
            (os.path.join(basedir, 'templates'),'ecs-simple-webapp.yml')]
        self.project.set_property('bucket_name', self.bucket_name)
        self.project.set_property('template_key_prefix', 'palp/')
        self.project.set_property('template_files', self.test_files)
        self.project.set_property(
                'template_file_access_control', 'bucket-owner-full-control')
        self.my_mock_s3 = mock_s3()
        self.my_mock_s3.start()
        self.s3 = boto3.resource('s3')
        self.s3.create_bucket(Bucket=self.bucket_name)

    def tearDown(self):
        self.my_mock_s3.stop()


class UploadJSONToS3(TestsWithS3):

    def test_upload_cfn_files(self):
        upload_cfn_to_s3(self.project, mock.MagicMock(Logger))
        s3_object_list = [
            o for o in self.s3.Bucket(self.bucket_name).objects.all()]

        key_prefix = self.project.get_property('template_key_prefix')
        self.assertEqual(s3_object_list[0].bucket_name, self.bucket_name)
        keys = [o.key for o in s3_object_list]
        for test_file in self.test_files:
            version_path = '{0}v{1}/{2}'.format(
                    key_prefix, self.project.version,
                    test_file[1].replace('yml', 'json'))
            self.assertTrue(version_path in keys,
                            "Key {0} not found in {1}".format(version_path, keys))
            s3_grants=self.s3.Object(
                    bucket_name=self.bucket_name, key=version_path).Acl().grants
            self.assertDictContainsSubset({"Permission":"FULL_CONTROL"},s3_grants[0])

    def test_upload_fails_with_invalid_acl_value(self):
        self.project.set_property('template_file_access_control',
                                  'no_such_value')
        self.assertRaises(BuildFailedException,
                          upload_cfn_to_s3,
                          self.project,
                          mock.MagicMock(Logger))


class CfnReleaseTests(TestsWithS3):

    def test_release_successful(self):
        upload_cfn_to_s3(self.project, mock.MagicMock(Logger))
        cfn_release(self.project, mock.MagicMock(Logger))
        key_prefix = self.project.get_property('template_key_prefix')
        s3_keys = [o.key for o in self.s3.Bucket(self.bucket_name).objects.all()]
        for (path,filename) in self.test_files:
            key_path = '{0}latest/{1}'.format(
                    key_prefix, filename.replace('yml', 'json'))
            self.assertTrue(key_path in s3_keys,
                            "Key {0} not found in {1}".format(key_path, s3_keys))
            s3_grants=self.s3.Object(
                    bucket_name=self.bucket_name, key=key_path).Acl().grants
            self.assertDictContainsSubset({"Permission":"FULL_CONTROL"},s3_grants[0])

