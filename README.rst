.. image:: https://travis-ci.org/ImmobilienScout24/pybuilder_aws_plugin.svg?branch=master
    :target: https://travis-ci.org/ImmobilienScout24/pybuilder_aws_plugin

.. image:: https://coveralls.io/repos/ImmobilienScout24/pybuilder_aws_plugin/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/ImmobilienScout24/pybuilder_aws_plugin?branch=master

.. image:: https://badge.fury.io/py/pybuilder_aws_plugin.svg
    :target: https://badge.fury.io/py/pybuilder_aws_plugin


====================
pybuilder_aws_plugin
====================

PyBuilder plugin to simplify building projects for Amazon Web Services. The
following use cases are supported:

* Packaging Python code for Lambda_ and uploading the result to S3_.
* Maintain CloudFormation templates in YAML_ and upload to S3_. Conversion done
  with cfn-sphere_.
* Deploy code and templates for a `CloudFormation custom resource backed by a
  Lambda function`__.

.. _Lambda: https://aws.amazon.com/documentation/lambda/
.. _S3: http://aws.amazon.com/documentation/s3/
.. _YAML: http://yaml.org/
.. _cfn-sphere: https://github.com/cfn-sphere/cfn-sphere
.. __: http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-lambda.html

Incompatible Changes
====================

>161 (March 2016) Upload and Release are Separate Steps
-------------------------------------------------------

Till up to version 161 ``upload_zip_to_s3`` and ``upload_cfn_to_s3`` tasks
would upload the files to S3 both under a versioned (``v123``) path and under a
``latest`` path element. This behavior prevents testing the new version before
releasing it under the ``latest`` path.

Since the task name "upload" does not imply "release" and since we believe in
`Test Driven Development`__ we decided to break backwards compatibility in this
case.

From version 162 and onward the "upload" tasks will only upload files to S3
under a versioned path. We provide two new tasks ``lambda_release`` and
``cfn_release`` to explicitly copy the files from the versioned path to the
``latest`` path.

We apologize for the inconvenience and hope that this change will simplify your
integration tests.

.. __: https://en.wikipedia.org/wiki/Test-driven_development

Usage
=====================

Add the following plugin dependency to your ``build.py`` (will install directly
from PyPi):

.. code:: python

    use_plugin('pypi:pybuilder_aws_plugin')

After this you have the following additional tasks, which are explained below:

* ``package_lambda_code``
* ``upload_zip_to_s3``
* ``upload_cfn_to_s3``
* ``lambda_release``
* ``cfn_release``
* ``upload_custom_resource``
* ``release_custom_resource``

@Task: package_lambda_code
--------------------------
This task `assembles the Zip-file`__ (a.k.a. the *lambda-zip*) which will be
uploaded to S3_ with the task ``upload_zip_to_s3``. This task consists of the
following steps:

.. __: http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html

Add all dependencies
~~~~~~~~~~~~~~~~~~~~~~~~
Install every entry in ``build.py``, that is specified by using
``project.depends_on()``, into a temporary directory via ``pip install -t``.
These will be included in the resulting lambda-zip. Set the project property
``install_dependencies_index_url`` to use a custom index url (e.g. an internal
`PYPI server`__).

**Note:** This excludes `boto` and `boto3` as they are included in `AWS lambda dependencies`__ by default

.. __: http://doc.devpi.net/latest/
.. __: http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html

Add all own modules
~~~~~~~~~~~~~~~~~~~~~~~
All modules which are found in ``src/main/python/`` are copied directly into
the lambda-zip.

Add all script files
~~~~~~~~~~~~~~~~~~~~~~~~
The content of the scripts folder (``src/main/scripts``) in a PyBuilder project
is normally intended to be placed in ``/usr/bin``. This plugin assumes this
directory contains scripts including the lambda handler functions. Therefore
all files under this folder are copied directly to the root directory (``/``)
of the lambda-zip.

Pack everything into the Zip-file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All these files are packed as a Zip-file that complies with the Lambda_
specification.

@Task: upload_zip_to_s3
-----------------------
This task uploads the generated zip to an S3_ bucket. The bucket name is set in
``build.py``:

.. code:: python

    project.set_property('bucket_name', 'my_lambda_bucket')

The default acl for zips to be uploaded is ``bucket-owner-full-control``. But
if you need another acl you can overwrite this as follows in ``build.py``:

.. code:: python

    project.set_property('lambda_file_access_control', '<acl>')

.. _acl:

Possible acl values are:

* ``private``
* ``public-read``
* ``public-read-write``
* ``authenticated-read``
* ``bucket-owner-read``
* ``bucket-owner-full-control``

Furthermore, the plugin assumes that you already have a shell with enabled AWS
access (exported keys or .boto or ...). `afp-cli
<https://github.com/ImmobilienScout24/afp-cli>`_ is a tool to provide temporary
credentials for shell users.

The uploaded files will be placed in a directory with the version number like:
``v123/projectname.zip``.

Use the property ``bucket_prefix`` to add a prefix to the uploaded
files. For example:

.. code:: python

   project.set_property('bucket_prefix', 'my_lambda/')

This will upload the zip-file to the following key:
``my_lambda/v123/projectname.zip``

On TeamCity_ you can enable setting a TeamCity build parameter with the key of
the uploaded zip-file:

.. _TeamCity: https://www.jetbrains.com/teamcity/
.. code::python

    project.set_property('teamcity_output', True)
    project.set_property('teamcity_parameter', 'my_tc_parameter')

After uploading the zip-file to S3_ the plugin will emit a

.. code::

    ##teamcity[setParameter name='my_tc_parameter' value='my_lambda/v123/project-name.zip']

line which TeamCity can parse. You can then use the value in other build steps.

@Task: upload_cfn_to_s3
-----------------------

NOTE: This task is available for Python 2.7 and up, due to cfn-sphere_
dependencies not being available for Python 2.6.

This task converts and uploads the CFN-Sphere template YAML_ files as JSON_ to
a S3_ bucket.  Set the bucket name in ``build.py``:

.. _JSON: http://www.json.org/
.. code:: python

    project.set_property('bucket_name', 'my_template_bucket')

Define the CFN templates to upload via a list of
tuples in the ``template_files`` property:

.. code:: python

    project.set_property('template_files',
        [
            ('path1','filename1.yaml'),
            ('path2','filename2.yaml'),
            ...
        ])

The uploaded files will be placed in a directory with the version number:

- ``v123/filename1.json``
- ``v123/filename2.json``

Use the property ``template_key_prefix`` to add a prefix to the uploaded
files. For example:

.. code:: python

   project.set_property('template_key_prefix', 'my_template/')

This will upload the files to the following files:

- ``my_template/v123/filename1.json``
- ``my_template/v123/filename2.json``


The ACL for the JSON_ files is ``bucket-owner-full-control``. Set another ACL
in ``build.py``:

.. code:: python

    project.set_property('template_file_access_control', '<acl>')

Possible acl values are:

* ``private``
* ``public-read``
* ``public-read-write``
* ``authenticated-read``
* ``bucket-owner-read``
* ``bucket-owner-full-control``

@Task: lambda_release, cfn_release
-----------------------------------

These tasks copy the lambda-zip or CFN template files from the versioned path
to version independant path named ``latest``. For Example:

- ``my_lambda/v123/my-project.zip`` is copied to ``my_lambda/latest/my-project.zip``
- ``my_templates/v123/my-cfn.json`` is copied to ``my_templates/latest/my-cfn.json``

This provides a simple release mechanism that follows the "latest greatest"
principle. Users can rely on the files under ``latest`` to be the latest tested
version.

@Task: upload_custom_resource, release_custom_resource
------------------------------------------------------

For CloudFormation custom resources backed by a Lambda function these two tasks
provide convenience wrappers to implement an "Update - Test - Release" process:

.. code:: shell

    #!/bin/bash
    set -e
    pyb upload_custom_resource
    ./run-integration-test.py
    pyb release_custom_resource

The ``upload_custom_resource`` task bundles the ``upload_zip_to_s3`` and the
``upload_cfn_to_s3`` task. It is strongly recmomended to *not* use a
``bucket_prefix`` in order to keep the lambda-zip and CFN templates in the same
direcory on S3.

Licence
=======

Copyright 2015,2016 Immobilien Scout GmbH

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
