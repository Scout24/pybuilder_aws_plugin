from pybuilder.core import use_plugin, init, Author
from pybuilder.vcs import VCSRevision

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
# use_plugin("python.coverage")
use_plugin("python.distutils")


name = "pybuilder_aws_lambda_plugin"
default_task = "publish"
version = VCSRevision().get_git_revision_count()
summary = "PyBuilder plugin to handle packaging and uploading Python AWS Lambda code."
authors = [Author('Valentin Haenel', 'valentin@haenel.co'),
           Author('Stefan Neben',    'stefan.neben@gmail.com'),
           ]
license = 'Apache'
url = 'https://github.com/ImmobilienScout24/pybuilder_aws_lambda_plugin'


@init
def set_properties(project):
    project.set_property('install_dependencies_upgrade', True)
    project.set_property('distutils_classifiers', [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: Utilities',
    ])
