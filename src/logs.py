#!/usr/bin/env python3
""" Utilities for cataloging and searching log-like data """

# commands:
# logs info  # show what I currently have in local persistence
# logs use [url] [url] ..  # pull external things into local persistence
#                          # eg the architecture file
# logs query "sparql query"  # run an arbitrary sparql query
# logs find <something>    # return which parts of which logs have something
# logs catalog <thing>     # create an rdf catalog 

import config
import argparse
import commands
import sys

if __name__ == '__main__':
    desc = __doc__
    parser = argparse.ArgumentParser(description=desc)
    config.setup_global_args(parser)
    subparsers = parser.add_subparsers(dest='command')
    for c in commands.commands.values():
        c.setup_args(subparsers)

    args = sys.argv[1:]
    if len(args) < 1:
        parser.print_help()
        parser.exit()

    params = vars(parser.parse_args(args)).copy()

    config.update_settings(params)
    cmd = params['command']
    commands.commands[cmd].run(params)


