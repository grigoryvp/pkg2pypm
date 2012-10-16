#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

import argparse

def main() :
  oParser = argparse.ArgumentParser( description = "PYPI to PYPM converter" )
  oParser.add_argument( 'source', help = "PYPI .tar.gz file or directory" )
  oParser.add_argument( 'target', help = "PYPM .pypm file to create" )
  oArgs = oParser.parse_args()
  if oArgs.source.isfile() and oArgs.source.endswith( 'tar.gz' ) :
    pass

