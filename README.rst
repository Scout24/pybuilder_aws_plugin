.. image:: https://travis-ci.org/ImmobilienScout24/pybuilder_aws_lambda_plugin.svg?branch=master
    :target: https://travis-ci.org/ImmobilienScout24/pybuilder_aws_lambda_plugin

===========================
pybuilder_aws_lambda_plugin
===========================

PyBuilder plugin to handle packaging and uploading Python AWS Lambda code.

How to use the Plugin
---------------------

Add plugin dependency to your ``build.py``:

.. code:: python

    use_plugin('pypi:pybuilder_aws_lambda_plugin')

And ...

.. code:: console

    $ pyb package_lambda_code
    ...
    $ pyb upload_zip_to_s3
    ...


Licence
-------

Copyright 2015 Immobilienscout24 GmbH

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

