#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

import os
import sys
import argparse
import tempfile
import shutil
import gzip
import tarfile
import distutils.dir_util
import subprocess
import rfc822

ABOUT_APP = "PYPI to PYPM converter"

def getDirMeta( dirpackage ) :
  for sDir in os.listdir( dirpackage ) :
    sDir = os.path.join( dirpackage, sDir )
    if os.path.isdir( sDir ) and sDir.endswith( '.egg-info' ) :
      return sDir

def main() :
  try :
    ##  Used to extract ".tar.gz" into or copy package directory to run
    ##  it's 'setup.py' and create metadata.
    sDirTmp = tempfile.mkdtemp()
    oParser = argparse.ArgumentParser( description = ABOUT_APP )
    oParser.add_argument( 'source', help = "PYPI .tar.gz file or directory" )
    oParser.add_argument( 'target', help = "PYPM .pypm file to create" )
    oArgs = oParser.parse_args()
    if os.path.isfile( oArgs.source ) :
      assert oArgs.source.endswith( 'tar.gz' ), "Source file must be .tar.gz"
      sFileTmp = '{0}/pkg.tar'.format( sDirTmp )
      ##  Extract '.tar' from 'tar.gz'
      with open( sFileTmp, 'wb' ) as oDst :
        with gzip.open( oArgs.source ) as oSrc :
          oDst.write( oSrc.read() )
      ##  Extract content of '.tar'
      with tarfile.open( sFileTmp ) as oSrc :
        oSrc.extractall( sDirTmp )
      os.remove( sFileTmp )
      ##  Single folder inside temp dir is the package from '.tar.gz'
      lContent = os.listdir( sDirTmp )
      assert len( lContent ) == 1, ".tar must contain one root item"
      sDirPkg = os.path.join( sDirTmp, lContent[ 0 ] )
      assert os.path.isdir( sDirPkg ), ".tar must contain directory"
    else :
      distutils.dir_util.copy_tree( oArgs.source, sDirTmp )
      sDirPkg = sDirTmp
    ##  If package don't have '.egg-info' subdir with metadata than create it.
    if not getDirMeta( sDirPkg ) :
      subprocess.check_return( [
        'python',
        os.path.join( sDirPkg, 'setup.py' ),
        'sdist' ],
        ##! For 'python' to resolve.
        shell = True )
    sDirMeta = getDirMeta( sDirPkg )
    assert sDirMeta, "No .egg-info metadir and can't create one"
    ##  Read package metadata.
    with open( os.path.join( sDirMeta, 'PKG-INFO' ), 'rb' ) as oFile :
      ##! Names will be lowercase.
      mMeta = dict( rfc822.Message( oFile ).items() )
    print( "Name: \"{0}\"".format( mMeta[ 'name' ] ) )
  finally :
    shutil.rmtree( sDirTmp, ignore_errors = True )

