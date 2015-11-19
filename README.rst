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
Add plugin dependency to your ``build.py``:

.. code:: python

    use_plugin('pypi:pybuilder_aws_plugin')

After this you have the following additional tasks, which are explained below.

@Task: package_lambda_code
--------------------------
This task assembles the zip file which will be uploaded to S3 with the second
task. What is this task doing in detail?

Package all own modules
~~~~~~~~~~~~~~~~~~~~~~~
All modules which are found in ``src/main/python/`` where put directly into the
temporary folder, which will zipped later.

Package all dependencies
~~~~~~~~~~~~~~~~~~~~~~~~
Every entry in ``build.py`` with **depends_on** is installed into the zip
file. The target path for ``pip install`` points directly to the
temporary folder, which will then be zipped.

Package all script files
~~~~~~~~~~~~~~~~~~~~~~~~
The content in the scripts folder (``src/main/scripts``) of an pybuilder
project is normally intended to go to ``/usr/bin``. This plugin sees this folder
as a folder with script(s) including lambda handler functions. Therefore all
files under this folder are put at the root layer (``/``) of the zip file.

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

* private
* public-read
* public-read-write
* authenticated-read
* bucket-owner-read
* bucket-owner-full-control

Further the plugin assumes that you already have a shell with enabled aws
access (exported keys or .boto or ...). For that take a look at
e.g. `afp-cli <https://github.com/ImmobilienScout24/afp-cli>`_

The uploaded files will be placed in a directory with the version number,
and in a `latest/` directory, such as:

- `v123/projectname.zip`
- `latest/projectname.zip`

You can use the property ``bucket_prefix`` to add a prefix to the uploaded
files. For example:

.. code:: python

   project.set_property('bucket_prefix', 'my_lambda/')

This will upload the files to the following files:

- `my_lambda/v123/projectname.zip`
- `my_lambda/latest/projectname.zip`

In an TeamCity Environment (teamcity_output = True) you can use the property
``teamcity_parameter`` to push en ``##teamcity[setParameter name='' value='']``
event to TeamCity and rewrite this parameter with the name of the uploaded
zip file. For example:

.. code:: python

   project.set_property('teamcity_parameter', 'my_tc_parameter')

@Task: upload_cfn_to_s3
-----------------------
This task uploads the CFN-Sphere template files as JSON to a S3 bucket.
The bucket name is to be set as follows in ``build.py``:

.. code:: python

    project.set_property('bucket_name', 'my_lambda_bucket')

The default acl for JSON files to be uploaded is ``bucket-owner-full-control``.
But if you need another acl you can overwrite this as follows in ``build.py``:

.. code:: python

    project.set_property('template_file_access_control', '<wished_acl>')

To define the templates you wish to be uploaded set the property as a list of
tupels:

.. code:: python

    project.setProperty('template_files',
        [
            ('path1','filename1'),
            ('path2','filename2'),
            ...
        ])

The uploaded files will be placed in a directory with the version number,
and in a `latest/` directory, such as:

- `v123/filename1.json`
- `v123/filename2.json`
- `latest/filename1.json`
- `latest/filename2.json`

You can use the property ``template_key_prefix`` to add a prefix to the uploaded
files. For example:

.. code:: python

   project.set_property('template_key_prefix', 'my_lambda/')

This will upload the files to the following files:

- `my_lambda/v123/filename1.json`
- `my_lambda/v123/filename2.json`
- `my_lambda/latest/filename1.json`
- `my_lambda/latest/filename2.json`

NOTE: This task is available for Python 2.7 and up.

Licence
=======
Copyright 2015 Immobilienscout24 GmbH

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
