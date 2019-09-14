#!/usr/bin/env python
import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="logset",
    version="0.1.0",
    author="Steve Leak et al",
    author_email="sleak@lbl.gov",
    description="Utilities for dicovering and exploring HPC system logs",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/NERSC/LogSet",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    data_files=[
        ('etc', [
            'etc/ddict.ttl',
            'etc/defaults.toml',
            'etc/logset.ttl',
        ]),
        ('utils', [
            'utils/archFromInterconnect.pl'
        ]),
#        ('', [
#            'etc/ddict.ttl',
#            'etc/defaults.toml',
#            'etc/logset.ttl',
#            'utils/archFromInterconnect.pl'
#        ]),
    ],
    python_requires='>=3.6',
    install_requires=[
        'sqlalchemy',
        'rdflib_sqlalchemy',
        'rdflib',
        # used by LocalNSM:
        'bidict',
        # handles configuration/settings
        'toml',
        'deepmerge',
        # used in testing
        'behave']
)

