#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='overwatch-hub',
    version='0.0.1',
    author='Petr Messner',
    author_email='petr.messner@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(exclude=['doc', 'tests']),
    install_requires=[
        'aiohttp',
        'cchardet',
        'aiodns',
        'pyyaml',
        'simplejson',
    ],
    entry_points={
        'console_scripts': [
            'overwatch-hub=overwatch_hub:hub_main',
        ],
    },
)
