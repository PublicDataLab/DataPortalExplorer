#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read()

setup_requirements = []

test_requirements = []

setup(
    author="Kings Digital Lab",
    author_email='jmvieira@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    description="""This package contains tools to extract metadata from CKAN
    instances which can be used to study data portals as infrastructures from
    the perspective of social/cultural research.""",
    entry_points={
        'console_scripts': [
            'data_portal_explorer=data_portal_explorer.cli:cli',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='data_portal_explorer',
    name='data_portal_explorer',
    packages=find_packages(include=['data_portal_explorer']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://gitlab.com/kingsdigitallab/data_portal_explorer',
    version='0.1.0',
    zip_safe=False,
)
