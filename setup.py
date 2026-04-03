#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="unity-cli",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "unity-cli=unity_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
)
