#!/usr/bin/env python3

import sys
if sys.version_info < (3,6):
    raise Exception("Requires python 3.6+")

# I hate python's logging module:
import logging
#logging.basicConfig()
#logging.getLogger('').addHandler(logging.StreamHandler())
#logger = logging.getLogger(__name__)

import typing as t

import os
#FIXME: make this more elegant:
import pkg_resources
try:
    dist = pkg_resources.get_distribution('logset')
    etc: str = os.path.join(dist.location, 'etc')
    logging.info("found logset distribution at:")
    logging.info(etc)
except pkg_resources.DistributionNotFound:
    _installdir = os.path.join(os.path.dirname(__file__), '..', '..')
    logging.info(_installdir)
    installdir: str = os.path.abspath(_installdir)
    logging.info("no logset distribution, using:")
    etc: str = os.path.join(installdir, 'etc')
except:
    raise

import toml
import deepmerge

# TODO should make config forgiving wrt case sensitiy, eg interpret 'sqlite' as the 
#      user probably expects

settings: t.Dict[str,t.Any] = {}

for _path in (os.path.join(etc, "defaults.toml"),
              os.path.join(os.getenv('HOME') or '', ".logs.toml"),
              "logs.toml" ):
   if os.path.exists(_path):
        with open(_path) as f:
            deepmerge.always_merger.merge(settings, toml.load(f)) 

import bidict
_verbosity_levels = bidict.bidict({
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
})

def setup_global_args(parser):
    parser.add_argument('--no-local-persistence', '-n', dest='nolocal', default=False, 
        action='store_true', help="memory-only")
    parser.add_argument('--local-persistence', '-p', dest='dbpath',
        help="path to file or database for local (cached) log metadata",
        default=settings['persistence']['name'])

    parser.add_argument('-v', '--verbose', action='count', default=0,
        help="Be noisier. -vv is noisier than -v, etc")
    parser.add_argument('-q', '--quiet', action='count', default=0,
        help="Be quieter. -qq only shows critical errors")

import typing as t

def update_settings(params: t.Dict[str,str]):
    logging.debug(f"updating settings with: {params}")
    global settings

    if params['nolocal']:
        settings['persistence']['persistence'] = 'None'
    settings['persistence']['name'] = params['dbpath']

    verbosity_level = _verbosity_levels[settings['verbosity']]
    verbosity_level = verbosity_level + 10*params['quiet'] - 10*params['verbose']
    verbosity_level = max(logging.DEBUG, min(verbosity_level, logging.CRITICAL))
    settings['verbosity'] = _verbosity_levels.inverse[verbosity_level]

def apply_global_config():
    logging.getLogger().setLevel(_verbosity_levels[settings['verbosity']])
    #logging.basicConfig(level=_verbosity_levels[settings['verbosity']], format='%(message)s')
    #print("trying to apply logging level")

apply_global_config()
