#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

from setuptools import setup

setup(
  name         = "pkg2pypm",
  version      = '0.1.3',
  description  = "PYPI package to PYPM package converter.",
  author       = "Grigory Petrov",
  author_email = "grigory.v.p@gmail.com",
  url          = "http://bitbucket.org/eyeofhell/pkg2pypm",
  packages     = [ 'pkg2pypm' ],
  entry_points = { 'console_scripts' : [ 'pkg2pypm = pkg2pypm:main' ] },
  classifiers  = [
    'Development Status :: 1 - Prototype',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: GPLv3',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Utilities' ])

