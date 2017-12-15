#!/usr/bin/env python3
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
def parse_args(cmdline=sys.argv[1:]):
    import argparse
    desc=__doc__.split('\n',1)[0]
    parser = argparse.ArgumentParser(description=desc)

    # arguments common to all subcommands:
    parser.add_argument('--vocab', help="location of logset.ttl vocab file",
                        default='./')
    parser.add_argument('-l', '--loglevel', default='WARNING', metavar='LEVEL',
                        choices=['debug','d','info','i','warning','w',
                                 'error','e','critical','c'], 
                        help="noisiness of log output: "+
                             "(D)EBUG,(I)NFO,(W)ARNING,(E)RROR,(C)RITICAL",
                        type=str.lower)

    # parsers for subcommands:
    subs = parser.add_subparsers(title="subcommands",metavar="COMMAND", dest='command')
    for name,cls in commands.commands().items():
        cls.setup_parser(subs)

    if not cmdline:
         parser.print_help()
         return None 

    return parser.parse_args(cmdline)


import unittest
class TestArgParsing(unittest.TestCase):

    def test_basic_help(self):
        # capturing stdout from help, (thanks stackoverflow)
        import io
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput   # redirect to capture
        try:
            args = parse_args('-h'.split())
        except SystemExit:
            pass # we're testing, so don't abort completely!
        sys.stdout = sys.__stdout__   # reset redirect
        # beyond eyeballing it, I don't know how to meaningfully
        # check that the captured output is sensible, so this is
        # mostly a placeholder:
        logging.debug('\nCaptured:\n'+capturedOutput.getvalue())
        assert True


if __name__ == '__main__':

    args = parse_args()
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

