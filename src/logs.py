#!/usr/bin/env python3

import commands
import argparse
import logging
import sys
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="some usage text")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('-v','--verbose', action='count')
    common.add_argument('-u', '--url', nargs='+', action='append')
    subparsers = parser.add_subparsers()
    parser.set_defaults(func=help)

    import os
    p = os.path.dirname(os.path.abspath(__file__))
    p = p + os.sep + '../examples'
    eg_path = os.path.relpath(p)
    usage  = "some usage text\n"
    usage += "try this:\n"
    usage += "{0} catalog -n http://example.com/myindex ".format(sys.argv[0])
    usage += "-d {0}/p0-20170906t151820 ".format(eg_path)
    usage += "-u {0}/cray-dict.ttl -u {0}/nersc.ttl ".format(eg_path)

    for cmd in commands.commands:
#        usage += "{0:20s}{1}\n".format(cmd.command, cmd.purpose)
        cmd(subparsers, common)

    if len(sys.argv)==1:
        print(usage)
        sys.exit()

    args = parser.parse_args()
    if args.verbose:
        logger = logging.getLogger()
        level = logger.getEffectiveLevel() - 10*args.verbose
        logger.setLevel(level)
    args.func(args)
