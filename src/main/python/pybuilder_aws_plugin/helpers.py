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
            'Uploading to bucket "{0}" key {1}'
                .format(bucket_name, keyname))
    s3.Bucket(bucket_name).put_object(Key=keyname, Body=data, ACL=acl)


def copy_helper(logger, bucket_name, source_key, destination_key, acl):
    'Copy S3 source_key to destination_key in bucket_name applying acl'
    logger.info('Copying in {0} from {1} to {2}'.format(bucket_name, source_key, destination_key))
    client = boto3.client('s3')
    client.copy_object(ACL=acl,
                       Bucket=bucket_name,
                       CopySource={'Bucket': bucket_name,
                                   'Key':    source_key
                                   },
                       Key=destination_key,
                       MetadataDirective='COPY')


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

# copied from https://github.com/JetBrains/teamcity-messages/blob/942584909b2ce51e62a7c3360c5e1d1af6e1ef5a/teamcity/messages.py#L13
_quote = {"'": "|'", "|": "||", "\n": "|n", "\r": "|r", '[': '|[', ']': '|]'}


def _teamcity_escape_value(value):
    return "".join(_quote.get(x, x) for x in value)


def teamcity_append_build_status(text):
    flush_text_line(
        "##teamcity[buildStatus text='{build.status.text} %s']" % _teamcity_escape_value(text)
    )