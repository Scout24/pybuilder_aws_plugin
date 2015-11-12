import os
import mock
from unittest import TestCase

import boto3
from moto import mock_s3
from pybuilder.core import Logger, Project
from pybuilder_aws_lambda_plugin import upload_cfn_to_s3


class UploadJSONToS3(TestCase):
    """
    These tests are separate since they only work with Python2 >2.6 by
    the time being. Python3 support is underway.
    """

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

    def test_upload_cfn_fils(self):
        upload_cfn_to_s3(self.project, mock.MagicMock(Logger))
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
