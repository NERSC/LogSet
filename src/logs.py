#!/usr/bin/env python3

import logging

import sys
logging.debug(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

sys.path.append('/global/homes/s/sleak/Monitoring/Resilience/LogSet/src')


import argparse
from abc import ABC
class Command(ABC):
    #command = ''
    #usage = ''
    def __init__(self, subparsers):
        self.parser = subparsers.add_parser(self.command, help=self.usage)
        self.parser.set_defaults(func=self.execute)

    def execute(self, args):
        print("executing {0} with args {1}".format(self.__class__.__name__, str(args)))

class CatalogCommand(Command):
    command = "catalog"
    usage = "catalog <directory>"

    def __init__(self, subparsers):
        super().__init__(subparsers)
        h = "url of catalog to add new index to (or create if necessary)"
        self.parser.add_argument('-c', '--catalog', nargs=1, required=True, help=h)
        h = "namespace for the new index"
        self.parser.add_argument('-n', '--namespace', nargs=1, required=True, help=h)
        h = "a label for the new index (gets used in filename too)"
        self.parser.add_argument('-l', '--label', nargs=1, required=True, help=h)
        h = "path to scan for logfiles to index"
        self.parser.add_argument('-p', '--path', nargs=1, required=True, help=h)

    def execute(self, args):
        catalog = args.catalog[0]
        path = args.path[0]
        label = args.label[0]
        ns = args.namespace[0]

        # maybe adding the index should be last, user is more prepared to 
        # answer questions about it
        newindex = LogSet.LogSet(ns+label)
        for triple in newindex.tripes():
            LogsGraph.graph.add(triple)

        # if we do one logseries at a time, then the ordering can be 
        # handled within the logseries (and assume that nothing has a
        # catchall pattern?)
        # filename patterns:
        todo = set([p for p in Logseries.known_filename_patterns()])
        done = set()
        # (relative_path, filename) pairs:
        baselen = len(path)+1
        remaining = set([(base[baselen:],f) for base, d, files in os.walk(path) for f in files])

        while len(todo) > 0:
            for pattern in sorted(todo, key=len, reverse=True):
                logseries = LogSeries.logseries_for_filename_pattern(pattern)
                matching = logseries.candiates(remaining):
                for f in matching:
                    log = ConcreteLog(f, logseries,...)
                    log.add_to_graph()
                remaining -= matching
                done.add(pattern)
                todo.remove(pattern)
            # next, with remaining files, find a suitable logseries (or define one)
            # .. and add it to todo then return to that loop
            # might sometimes need to defer/skip a file 


class AvailCommand(Command):
    """ avail: Show what types of logs are available/cataloged, for what systems
        and over what time periods
    """
    command = "avail" 
    usage = "avail"

    def __init__(self, subparsers):
        super().__init__(subparsers)


class FindCommand(Command):
    command = "find"
    usage = "find [-t <logtypes>] [-s <subjects>] "
    def __init__(self, subparsers):
        super().__init__(subparsers)
    


if __name__ == '__main__':
    eg_dir = "/global/cscratch1/sd/sleak/Resilience/corismw-sample-p0/p0-20170906t151820"
    eg_ns  = "http://example.org/myindex#"
    eg_cat = "./example-cat.ttl"
    eg_label = "newindex"
    desc  = "\nFor example:"
    desc += "{0} catalog -d {1} -n {2} -c {3} -l {4}".format(sys.argv[0], 
            eg_dir, eg_ns, eg_cat, eg_label)
    if len(sys.argv)==1:
        print(desc)
        sys.exit()
    parser = argparse.ArgumentParser(desc)
    parser.add_argument('-v','--verbose', action='count')
    parser.add_argument('-u', '--urls', nargs='*')
    parser.set_defaults(func=help)
    subparsers = parser.add_subparsers()
    for cmd in CatalogCommand,FindCommand:
        cmd(subparsers)
    args = parser. parse_args()
    args.func(args)

