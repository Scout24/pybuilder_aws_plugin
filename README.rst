.. image:: https://travis-ci.org/ImmobilienScout24/pybuilder_aws_plugin.svg?branch=master
    :target: https://travis-ci.org/ImmobilienScout24/pybuilder_aws_plugin

.. image:: https://coveralls.io/repos/ImmobilienScout24/pybuilder_aws_plugin/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/ImmobilienScout24/pybuilder_aws_plugin?branch=master

.. image:: https://badge.fury.io/py/pybuilder_aws_plugin.svg
    :target: https://badge.fury.io/py/pybuilder_aws_plugin


====================
pybuilder_aws_plugin
====================

PyBuilder plugin to handle AWS functionality.

How to use the Plugin
=====================
Add plugin dependency to your ``build.py`` (will install directly from PyPi):

.. code:: python

    use_plugin('pypi:pybuilder_aws_plugin')

After this you have the following additional tasks, which are explained below:

* ``package_lambda_code``
* ``upload_zip_to_s3``
* ``upload_cfn_to_s3``

@Task: package_lambda_code
--------------------------
This task assembles the Zip-file (a.k.a. the *lambda-zip*) which will be
uploaded to S3 with the task ``upload_zip_to_s3``. What is this task doing in
detail?

Package all dependencies
~~~~~~~~~~~~~~~~~~~~~~~~
Every entry in ``build.py`` that is specified by using ``project.depends_on``
is installed into a temporary directory  using ``pip install -t`` and are then
copied into the lambda-zip from there. The project property
``install_dependencies_index_url`` is respected and can be used to set a custom
index url (e.g. internal ``devpi``) for the installation.

Package all own modules
~~~~~~~~~~~~~~~~~~~~~~~
All modules which are found in ``src/main/python/`` are copied directly into
the lambda-zip.

Package all script files
~~~~~~~~~~~~~~~~~~~~~~~~
The content of the scripts folder (``src/main/scripts``) in a PyBuilder project
is normally intended to be placed in ``/usr/bin``. This plugin assumes this
directory contains script(s) including the lambda handler functions. Therefore
all files under this folder are copied directly to the root layer (``/``) of
the lambda-zip.

@Task: upload_zip_to_s3
-----------------------
This task uploads the generated zip to a S3 bucket. The bucket name is to be
set as follows in ``build.py``:

.. code:: python

    project.set_property('bucket_name', 'my_lambda_bucket')

The default acl for zips to be uploaded is ``bucket-owner-full-control``. But
if you need another acl you can overwrite this as follows in ``build.py``:

.. code:: python

    project.set_property('lambda_file_access_control', '<wished_acl>')

Possible acl values are:

* ``private``
* ``public-read``
* ``public-read-write``
* ``authenticated-read``
* ``bucket-owner-read``
* ``bucket-owner-full-control``

Further, the plugin assumes that you already have a shell with enabled aws
access (exported keys or .boto or ...). For that take a look at
e.g. `afp-cli <https://github.com/ImmobilienScout24/afp-cli>`_

The uploaded files will be placed in a directory with the version number,
and in a ``latest/`` directory, such as:

- ``v123/projectname.zip``
- ``latest/projectname.zip``

You can use the property ``bucket_prefix`` to add a prefix to the uploaded
files. For example:

.. code:: python

   project.set_property('bucket_prefix', 'my_lambda/')

This will upload the files to the following files:

- ``my_lambda/v123/projectname.zip``
- ``my_lambda/latest/projectname.zip``

In an TeamCity Environment (teamcity_output = True) you can use the property
``teamcity_parameter`` to push en ``##teamcity[setParameter name='' value='']``
event to TeamCity and rewrite this parameter with the name of the uploaded
zip file. For example:

.. code:: python

   project.set_property('teamcity_parameter', 'my_tc_parameter')

@Task: upload_cfn_to_s3
-----------------------


NOTE: This task is available for Python 2.7 and up, due to CFN-Sphere
dependencies not being available for Python 2.6.

This task converts and uploads the CFN-Sphere template YAML files as JSON to a
S3 bucket.  The bucket name is to be set as follows in ``build.py``:

.. code:: python

    project.set_property('bucket_name', 'my_template_bucket')

The default acl for JSON files to be uploaded is ``bucket-owner-full-control``.
But if you need another acl you can overwrite this as follows in ``build.py``:

.. code:: python

    project.set_property('template_file_access_control', '<wished_acl>')

To define the templates you wish to be uploaded set the property as a list of
tupels:

.. code:: python

    project.set_property('template_files',
        [
            ('path1','filename1'),
            ('path2','filename2'),
            ...
        ])

The uploaded files will be placed in a directory with the version number,
and in a ``latest/`` directory, such as:

- ``v123/filename1.json``
- ``v123/filename2.json``
- ``latest/filename1.json``
- ``latest/filename2.json``

You can use the property ``template_key_prefix`` to add a prefix to the uploaded
files. For example:

.. code:: python

   project.set_property('template_key_prefix', 'my_template/')

This will upload the files to the following files:

- ``my_template/v123/filename1.json``
- ``my_template/v123/filename2.json``
- ``my_template/latest/filename1.json``
- ``my_template/latest/filename2.json``


The default acl for templates to be uploaded is ``bucket-owner-full-control``.
But if you need another acl you can overwrite this as follows in ``build.py``:

.. code:: python

    project.set_property('template_file_access_control', '<wished_acl>')

Possible acl values are:

* ``private``
* ``public-read``
* ``public-read-write``
* ``authenticated-read``
* ``bucket-owner-read``
* ``bucket-owner-full-control``

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
