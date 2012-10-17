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
import json
import zipfile

ABOUT_APP = "PYPI to PYPM converter"

def getDirMeta( dirpackage ) :
  for sDir in os.listdir( dirpackage ) :
    sDir = os.path.join( dirpackage, sDir )
    if os.path.isdir( sDir ) and sDir.endswith( '.egg-info' ) :
      return sDir

def convertMetadata( subject ) :
  ##* Architecure need to be passed to script.
  ##* Python version need to be passed to script.
  mDst = { 'pkg_version' : 1, 'osarch' : 'win32-x86', 'pyver' : '2.7' }
  def convertRecord( name, sourcename = None ) :
    mDst[ name ] = subject.get( sourcename or name )
  convertRecord( 'maintainer' )
  convertRecord( 'description' )
  convertRecord( 'license' )
  convertRecord( 'author' )
  convertRecord( 'home_page', 'home-page' )
  convertRecord( 'summary' )
  convertRecord( 'author_email', 'author-email' )
  convertRecord( 'version' )
  convertRecord( 'keywords' )
  convertRecord( 'install_requires' )
  convertRecord( 'maintainer_email' )
  convertRecord( 'name' )
  return mDst

def main() :
  try :
    ##  Used to extract ".tar.gz" into or copy package directory to run
    ##  it's 'setup.py' and create metadata.
    sDirTmpPkg = tempfile.mkdtemp()
    ##  Used to create PYPM package directory structure before packing
    ##  it into .pypm file that is actually a .tar.gz archive.
    sDirTmpPypm = tempfile.mkdtemp()
    ##  Used to repack archive created by 'setup.py'
    sDirTmpRepack = tempfile.mkdtemp()
    oParser = argparse.ArgumentParser( description = ABOUT_APP )
    oParser.add_argument( 'source', help = "PYPI .tar.gz file or directory" )
    oParser.add_argument( 'target', help = "PYPM .pypm file to create" )
    oArgs = oParser.parse_args()
    ##! Script will change current dir, so use absolute paths.
    oArgs.source = os.path.abspath( oArgs.source )
    oArgs.target = os.path.abspath( oArgs.target )
    if os.path.isfile( oArgs.source ) :
      assert oArgs.source.endswith( 'tar.gz' ), "Source file must be .tar.gz"
      with tarfile.TarFile.gzopen( oArgs.source, 'rb' ) as oArchive :
        oArchive.extractall( sDirTmpPkg )
      ##  Single folder inside temp dir is the package from '.tar.gz'
      lContent = os.listdir( sDirTmpPkg )
      assert len( lContent ) == 1, ".tar must contain one root item"
      sDirPkg = os.path.join( sDirTmpPkg, lContent[ 0 ] )
      assert os.path.isdir( sDirPkg ), ".tar must contain directory"
    else :
      distutils.dir_util.copy_tree( oArgs.source, sDirTmpPkg )
      sDirPkg = sDirTmpPkg
    ##  Create binary distribution in temp folder package was copied into.
    ##  This will create '.egg-info', 'build' and 'dist' dirs.
    ##! Requires for 'setup.py' to work.
    os.chdir( sDirPkg )
    subprocess.check_output( [
      'python',
      os.path.join( sDirPkg, 'setup.py' ),
      'bdist' ],
      ##! For 'python' to resolve.
      shell = True, stderr = subprocess.STDOUT )
    sDirMeta = getDirMeta( sDirPkg )
    assert sDirMeta, "No .egg-info metadir found"
    ##  Read package metadata.
    with open( os.path.join( sDirMeta, 'PKG-INFO' ), 'rb' ) as oFile :
      ##! Names will be lowercase.
      mMetaPkg = dict( rfc822.Message( oFile ).items() )
    ##  Create metadata for PYPM.
    with open( os.path.join( sDirTmpPypm, 'info.json' ), 'wb' ) as oFile :
      json.dump( convertMetadata( mMetaPkg ), oFile )
    ##  'bdist' command created 'bdist' dir with '.zip' archive that
    ##  contains dir like 'Python27' that contains 'Lib' and 'Scripts'
    ##  subdirs. PYPM pckage must contain 'data.tar.gz' archive that
    ##  contains 'Lib' and 'Scripts' as top level dirs. So, repack.
    lContent = os.listdir( os.path.join( sDirPkg, 'dist' ) )
    assert len( lContent ) == 1, "'bdist' dir must contain one item"
    sArchiveSrc = os.path.join( sDirPkg, 'dist', lContent[ 0 ] )
    with zipfile.ZipFile( sArchiveSrc ) as oArchiveSrc :
      oArchiveSrc.extractall( sDirTmpRepack )
      lContent = os.listdir( sDirTmpRepack )
      assert len( lContent ) == 1, "bdist .zip must contain one root item"
      sDirData = os.path.join( sDirTmpRepack, lContent[ 0 ] )
      assert os.path.isdir( sDirData ), "bdist .zip must contain directory"
      ##* Temp dir reuse is not good.
      sFileTar = os.path.join( sDirTmpPkg, 'data.tar' )
      with tarfile.TarFile( sFileTar, 'w' ) as oFileTar :
        ##! Requires for 'tar.add' to omit path.
        os.chdir( sDirData )
        for sDir in os.listdir( sDirData ) :
          oFileTar.add( sDir )
      sFileGzip = os.path.join( sDirTmpPypm, 'data.tar.gz' )
      with gzip.GzipFile( sFileGzip, 'w' ) as oFileGzip :
        with open( sFileTar, 'rb' ) as oFileTar :
          oFileGzip.write( oFileTar.read() )
    ##  Create PYPM package, it's a .tar.gz archive:
    sFileTar = os.path.join( sDirTmpPkg, 'data_out.tar' )
    with tarfile.TarFile( sFileTar, 'w' ) as oFileTar :
      ##! Requires for 'tar.add' to omit path.
      os.chdir( sDirTmpPypm )
      oFileTar.add( 'data.tar.gz' )
      oFileTar.add( 'info.json' )
    with gzip.GzipFile( oArgs.target, 'w' ) as oFileGzip :
      with open( sFileTar, 'rb' ) as oFileTar :
        oFileGzip.write( oFileTar.read() )
  finally :
    shutil.rmtree( sDirTmpPkg, ignore_errors = True )
    shutil.rmtree( sDirTmpPypm, ignore_errors = True )
    shutil.rmtree( sDirTmpRepack, ignore_errors = True )

