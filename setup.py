from __future__ import with_statement

from setuptools import setup, find_packages

from pyaxiom import __version__


def readme():
    with open('README.md') as f:
        return f.read()

reqs = [line.strip() for line in open('requirements.txt') if not line.startswith('#')]

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
