#!/usr/bin/env python
# coding:utf-8 vi:et:ts=2

# pkg2pypm core.
# Copyright 2013 Grigory Petrov
# See LICENSE for details.

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
import StringIO
import re

import info


def tarWriteStr( o_archive, s_name, s_data ) :
  oInfo = tarfile.TarInfo( name = s_name )
  oInfo.size = len( s_data )
  o_archive.addfile( oInfo, StringIO.StringIO( s_data ) )


def getDirMeta( s_dir ) :
  for sDir in os.listdir( s_dir ) :
    sDir = os.path.join( s_dir, sDir )
    if os.path.isdir( sDir ) and sDir.endswith( '.egg-info' ) :
      return sDir


def getOneFile( * l_args ) :
  sPath = os.path.join( * l_args )
  lContent = os.listdir( sPath )
  assert len( lContent ) == 1, "\"{0}\" must have one item".format( sPath )
  return os.path.join( sPath, lContent[ 0 ] )


def convertMetadata( m_metadata ) :
  ##* Architecure need to be passed to script.
  ##* Python version need to be passed to script.
  mDst = { 'pkg_version' : 1, 'osarch' : 'win32-x86', 'pyver' : '2.7' }
  def convertRecord( s_name, s_sourcename = None ) :
    mDst[ s_name ] = m_metadata.get( s_sourcename or s_name )
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
    oParser = argparse.ArgumentParser( description = info.DESCR )
    oParser.add_argument( 'source', help = "PYPI .tar.gz file or directory" )
    oParser.add_argument( 'target', help = "PYPM .pypm file to create" )
    oArgs = oParser.parse_args()
    ##! Script will change current dir, so use absolute paths.
    oArgs.source = os.path.abspath( oArgs.source )
    oArgs.target = os.path.abspath( oArgs.target )
    assert not os.path.isdir( oArgs.target ), "Target must be file, not dir"
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
    ##  Create PYPM package, it's a .tar.gz archive:
    with tarfile.TarFile.gzopen( oArgs.target, 'w' ) as oTarget :
      ##  Read source package data
      with zipfile.ZipFile( getOneFile( sDirPkg, 'dist' ) ) as oSource :
        ##  'bdist' command created 'bdist' dir with '.zip' archive that
        ##  contains dir like 'Python27' that contains 'Lib' and 'Scripts'
        ##  subdirs. PYPM pckage must contain 'data.tar.gz' archive that
        ##  contains 'Lib' and 'Scripts' as top level dirs. So, repack.
        oDataBits = StringIO.StringIO()
        mArgs = { 'fileobj' : oDataBits, 'mode' : 'w' }
        with tarfile.TarFile.gzopen( name = None, ** mArgs ) as oData :
          for oFile in oSource.filelist :
            ##! Skip first dir in source archive, it's like 'Python27'.
            sName = re.sub( r'^[^/\\]+(/|\\)', '', oFile.filename )
            tarWriteStr( oData, sName, oSource.read( oFile.filename ) )
        tarWriteStr( oTarget, 'data.tar.gz', oDataBits.getvalue() )
      # oTarget.add( 'data.tar.gz' )
      ##  Read source package metadata.
      sDirMeta = getDirMeta( sDirPkg )
      assert sDirMeta, "No .egg-info metadir found"
      with open( os.path.join( sDirMeta, 'PKG-INFO' ), 'rb' ) as oFile :
        ##  And write it into target package.
        ##! Names will be lowercase.
        sMetadata = convertMetadata( dict( rfc822.Message( oFile ).items() ) )
        tarWriteStr( oTarget, 'info.json', json.dumps( sMetadata ) )
  except Exception as oEx :
    print( "error: \"{0}\"".format( oEx.message ) )
  finally :
    shutil.rmtree( sDirTmpPkg, ignore_errors = True )

