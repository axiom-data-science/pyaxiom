from __future__ import with_statement
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from pyaxiom import __version__


def readme():
    with open('README.md') as f:
        return f.read()

reqs = [line.strip() for line in open('requirements.txt') if not line.startswith('#')]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name                = "pyaxiom",
    version             = __version__,
    description         = "An ocean data toolkit developed and used by Axiom Data Science",
    long_description    = readme(),
    license             = 'MIT',
    author              = "Kyle Wilcox",
    author_email        = "kyle@axiomdatascience.com",
    url                 = "https://github.com/axiom-data-science/pyaxiom",
    packages            = find_packages(),
    install_requires    = reqs,
    tests_require       = ['pytest'],
    cmdclass            = {'test': PyTest},
    entry_points        = {
        'console_scripts' : [
            'binner=pyaxiom.netcdf.grids.binner:run'
        ],
    },
    classifiers         = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
    ],
    include_package_data = True,
)
