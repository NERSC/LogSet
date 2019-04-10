#!/usr/bin/env python3

import sys
if sys.version_info < (3,6):
    raise Exception("Requires python 3.6+")

import os
_installdir = os.path.join(os.path.dirname(__file__), '..', '..')
installdir: str = os.path.abspath(_installdir)
etc: str = os.path.join(installdir, 'etc')

import toml
import deepmerge

settings = {}

for _path in (os.path.join(etc, "defaults.toml"),
              os.path.join(os.getenv('HOME'), ".logs.toml"),
              "logs.toml" ):
   if os.path.exists(_path):
        with open(_path) as f:
            deepmerge.always_merger.merge(settings, toml.load(f)) 

def setup_global_args(parser):
    parser.add_argument('--local-persistence', '-p', dest='dbpath',
        help="path to file or database for local (cached) log metadata",
        default=settings['persistence']['name'])

import typing as t

def update_settings(params: t.Dict[str,str]):
    global settings
    if 'dbpath' in params:
        settings['persistence']['name'] = params['dbpath']

