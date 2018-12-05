#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'requests>=2.18',
    'websocket-client>=0.47',
    # TODO: put package requirements here
]

setup_requirements = [
    'pytest-runner',
    # TODO(sdague): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    'pytest',
    'mock'
    # TODO: put package test requirements here
]

setup(
    name='waterfurnace',
    version='1.0.0',
    description="Python interface for waterfurnace geothermal systems",
    entry_points={
        'console_scripts': [
            'waterfurnace-debug=waterfurnace.cli:main'
        ]
    },
    long_description=readme + '\n\n' + history,
    author="Sean Dague",
    author_email='sean@dague.net',
    url='https://github.com/sdague/waterfurnace',
    packages=find_packages(include=['waterfurnace']),
    # TODO(sdague): bring back when we add a cli
    # entry_points={
    #     'console_scripts': [
    #         'waterfurnace=waterfurnace.cli:main'
    #     ]
    # },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='waterfurnace',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
