from setuptools import setup, find_packages
NAME = 'easy_cleaner'
VERSION = '1.0.1'
DESCRIPTION = 'Tools to clean Chinese/English Text'
AUTHOR = 'zbw'
AUTHOR_EMAIL = 'zbw292@126.com'
LICENSE = 'Apache License, Version 2.0'
PACKAGES = find_packages()
INSTALL_REQUIRES = [
    'numpy==1.19.2',
    'opencc==1.1.6',
    'urlextract==1.8.0',
    'fasttext'
]
with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    packages=PACKAGES,
    install_requires=INSTALL_REQUIRES,
    classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',  # Update this line
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
],
)

