#!/usr/bin/env python
###!/usr/bin/env python3
""" Utilities to manipulate LogSets for resilience-related analysis.

    2017-12-06 - WIP: still working out requirements etc. Some anticipated use
    cases are:

    .. code-block:: console

      $ logset help [<subcommand>]  # print relevant help and exit
      $ logset test [<test1> ...]   # run unit tests
      $ logset create <dir-or-tar>  # walk a dir or tar for logfiles and write
                                    # an index.ttl description, prompting user 
                                    # for input along the way
      $ logset info <dir-or-tar>    # report on contents and validity of logset
      $ logset add <files>          # just what it says
      $ logset pack [<location>]    # pack a logset into a .tgz with each 
                                    # LogSeries merged to a single file or dir,
                                    # and description, annotation files
      $ logset unpack <tarfile>     # expand logset back to its original form
      $ logset extract [<dates>] [<series>] <tarfile> # pull files from a packed
                                    # logset, optionally filtered to include 
                                    # only certain series and/or for a certain 
                                    # timespan, for processing by some external
                                    # analysis tool 
      $ logset annotate 

    For most (all) commands, the ability to pass everything on the command line 
    (as alternative to interactive) is probably valuable
"""

import logging

import sys
import commands

if __name__ == '__main__':

    args = commands.parse_args(desc=__doc__.split('\n',1)[0])
    logging.debug(commands.commands())
    if args and args.command:
        logging.debug('got args: ' + str(args))
        if args.loglevel:
            levels = { 'd': logging.DEBUG,
                       'i': logging.INFO, 
                       'w': logging.WARNING, 
                       'e': logging.ERROR, 
                       'c': logging.CRITICAL }
            logging.getLogger().setLevel(levels[args.loglevel[0]])
        #TODO handle other global/common args
        #if args.vocab:

        commands.commands()[args.command]().run(args)

