#!/usr/bin/env python

from setuptools import setup, find_packages

# with open('requirements.txt', encoding='utf-8') as f:
#     install_requires = f.read()

with open('README.md', encoding='utf-8') as f:
    readme = f.read()

# with open('LICENSE', encoding='utf-8') as f:
#     license = f.read()

entry_points = {
    'console_scripts': [
        'nepub = nepub.__main__:main'
    ]
}

setup(
    name='nepub',
    version='1.0.0',
    description='Small tool to convert Narou Novels to EPUB.',
    long_description=readme,
    author='tama@ttk1.net',
    author_email='tama@ttk1.net',
    url='https://github.com/ttk1/nepub',
    # license=license,
    # install_requires=install_requires,
    packages=find_packages(exclude=('test',)),
    entry_points=entry_points
)
