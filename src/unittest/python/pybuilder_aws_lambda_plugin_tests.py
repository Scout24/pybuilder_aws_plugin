#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mock
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
        self.project = Project("basedir")

    def test_if_file_was_uploaded_to_s3(self):

        project = mock.Mock()
        upload_zip_to_s3(project, mock.MagicMock(Logger))
