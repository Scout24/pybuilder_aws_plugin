#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
from pybuilder.ci_server_interaction import flush_text_line
from pybuilder.errors import BuildFailedException

permissible_acl_values = [
    'private',
    'public-read',
    'public-read-write',
    'authenticated-read',
    'bucket-owner-read',
    'bucket-owner-full-control',
]


def upload_helper(logger, bucket_name, keyname, data, acl):
    s3 = boto3.resource('s3')
    logger.info(
        'Uploading lambda-zip to bucket: "{0}" as key: "{1}"'
        .format(bucket_name, keyname))
    s3.Bucket(bucket_name).put_object(Key=keyname, Body=data, ACL=acl)


def check_acl_parameter_validity(property_, acl_value):
    if acl_value not in permissible_acl_values:
        raise BuildFailedException(
            "ACL value: '{0}' not allowed for property: '{1}'".
            format(acl_value, property_))


def teamcity_helper(tc_param, keyname):
    flush_text_line(
        "##teamcity[setParameter name='{0}' value='{1}']".format(
            tc_param, keyname
        ))
