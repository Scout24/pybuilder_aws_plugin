import boto3
from pybuilder.ci_server_interaction import flush_text_line


def upload_helper(logger, bucket_name, keyname, data, acl):
    s3 = boto3.resource('s3')
    logger.info(
        'Uploading lambda-zip to bucket: "{0}" as key: "{1}"'
        .format(bucket_name, keyname))
    s3.Bucket(bucket_name).put_object(Key=keyname, Body=data, ACL=acl)


def teamcity_helper(tc_param, keyname):
    flush_text_line(
        "##teamcity[setParameter name='{0}' value='{1}']".format(
            tc_param, keyname
        ))
