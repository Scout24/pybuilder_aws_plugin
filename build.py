#!/usr/bin/env python
#   -*- coding: utf-8 -*-
import sys
from pybuilder.core import Author, init, use_plugin
from pybuilder.vcs import VCSRevision

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")


name = "pybuilder_aws_plugin"
default_task = "publish"
version = VCSRevision().get_git_revision_count()
summary = "PyBuilder plugin to handle AWS functionality"
authors = [Author('Valentin Haenel', 'valentin@haenel.co'),
           Author('Stefan Neben',    'stefan.neben@gmail.com'),
           ]
license = 'Apache'
url = 'https://github.com/ImmobilienScout24/pybuilder_aws_plugin'


@init
def set_properties(project):
    project.set_property('install_dependencies_upgrade', True)
    project.depends_on("boto3")
    if sys.version_info[0:2] >= (2, 7):
        project.depends_on('cfn-sphere', '>=0.1.21')
    project.depends_on('httpretty', '<=0.8.11')
    project.build_depends_on("mock")
    project.build_depends_on("moto")
    project.set_property('coverage_break_build', False)
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
