#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

from wespe import __author__, __email__, __version__

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read().splitlines()

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author=__author__,
    author_email=__email__,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords=("wespe adtech marketing facebook google bing yandex facebook"),
    description="Batching ad tech providers’ operations for humans",
    install_requires=requirements,
    long_description=readme,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    name="wespe",
    packages=find_packages(
        include=["wespe", "wespe.*"], exclude=["*.tests", "*.tests.*"]
    ),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/kayak/wespe",
    version=__version__,
    zip_safe=False,
)
