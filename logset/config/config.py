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

# TODO should make config forgiving wrt case sensitiy, eg interpret 'sqlite' as the 
#      user probably expects

settings = {}

for _path in (os.path.join(etc, "defaults.toml"),
              os.path.join(os.getenv('HOME'), ".logs.toml"),
              "logs.toml" ):
   if os.path.exists(_path):
        with open(_path) as f:
            deepmerge.always_merger.merge(settings, toml.load(f)) 

import logging
logger = logging.getLogger(__name__)

import bidict
_verbosity_levels = bidict.bidict({
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
})

def setup_global_args(parser):
    parser.add_argument('--local-persistence', '-p', dest='dbpath',
        help="path to file or database for local (cached) log metadata",
        default=settings['persistence']['name'])

    parser.add_argument('-v', '--verbose', action='count', default=0,
        help="Be noisier. -vv is noisier than -v, etc")
    parser.add_argument('-q', '--quiet', action='count', default=0,
        help="Be quieter. -qq only shows critical errors")

import typing as t

def update_settings(params: t.Dict[str,str]):
    logger.debug(f"updating settings with: {params}")
    global settings

    settings['persistence']['name'] = params['dbpath']

    verbosity_level = _verbosity_levels[settings['verbosity']]
    verbosity_level = verbosity_level + 10*params['quiet'] - 10*params['verbose']
    verbosity_level = max(logging.DEBUG, min(verbosity_level, logging.CRITICAL))
    settings['verbosity'] = _verbosity_levels.inverse[verbosity_level]

def apply_global_config():
    logging.getLogger().setLevel(_verbosity_levels[settings['verbosity']])

apply_global_config()
