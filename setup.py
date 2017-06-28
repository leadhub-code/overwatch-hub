#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='overwatch-hub',
    version='0.0.1',
    license='MIT',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'flask',
        'pymongo',
        'pyyaml',
    ],
)
