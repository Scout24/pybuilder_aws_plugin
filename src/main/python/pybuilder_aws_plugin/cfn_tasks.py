from .helpers import upload_helper
from pybuilder.core import task


@task('upload_cfn_to_s3',
      description='Convert & upload CloudFormation templates in JSON '
      'created out of the CFN-Sphere template YAML files')
def upload_cfn_to_s3(project, logger):
    """
    This task is separate since they only work with Python2 >2.6 by
    the time being. Python3 support is underway.

    This means, when using Python<2.7, this task is not visible
    (see __init__.py).
    """
    from cfn_sphere.aws.cloudformation.template_loader import (
        CloudFormationTemplateLoader)
    from cfn_sphere.aws.cloudformation.template_transformer import (
        CloudFormationTemplateTransformer)

    for path, filename in project.get_property('template_files'):
        template = CloudFormationTemplateLoader.get_template_from_url(
            filename, path)
        transformed = CloudFormationTemplateTransformer.transform_template(
            template)
        output = transformed.get_template_json()

        bucket_name = project.get_property('bucket_name')
        key_prefix = project.get_property('template_key_prefix')
        filename = filename.replace('.yml', '.json')
        filename = filename.replace('.yaml', '.json')
        version_path = '{0}v{1}/{2}'.format(
            key_prefix, project.version, filename)
        latest_path = '{0}latest/{1}'.format(key_prefix, filename)

        acl = project.get_property('template_file_access_control')
        upload_helper(logger, bucket_name, version_path, output, acl)
        upload_helper(logger, bucket_name, latest_path, output, acl)
