#!/usr/bin/env python3

import logging

import sys
logging.debug(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

sys.path.append('/global/homes/s/sleak/Monitoring/Resilience/LogSet/src')

import argparse

from collections import namedtuple
ArgDetails = namedtuple('ArgDetails', 'short, long, nargs, required, help, example')

from abc import ABC
class Command(ABC):
    command = ''
    usage = ''
    _args = []
    def __init__(self, subparsers):
        self.parser = subparsers.add_parser(self.command, help=self.usage, epilog=self.epilog())
        for arg in self._args:
            self.parser.add_argument(arg.short, arg.long, arg.nargs, arg,required, arg.help)
        self.parser.set_defaults(func=self.execute)

    @classmethod
    def epilog(cls):
        """ return some epilog help for this command """
        txt  = "{0} {1}".format(sys.argv[0], self.command)
        for arg in self._args:
            txt += ' {}'.format(arg.example)
        return txt

    def execute(self, args):
        print("executing {0} with args {1}".format(self.__class__.__name__, str(args)))

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
    

from LogSeries import FileInfo

class CatalogCommand(Command):
    command = "catalog"
    usage = "catalog <directory>"

    _args = [ ArgDetails(
                '-c', '--catalog', 1, False, "url of catalog to update", 
                "-c ./example-cat.ttl" ),
              ArgDetails(
                '-n', '--namespace', 1, True, "namespace for this new dataset",
                "-n http://example.org/myindex#" ),
              ArgDetails(
                '-d', '--dir', 1, True, "directory to scan for log files to catalog",
                "-d /global/cscratch1/sd/sleak/Resilience/corismw-sample-p0/p0-20170906t151820")
            ]
        
    def execute(self, args):
        catalog = args.catalog[0]
        topdir = args.dir[0]
        ns = rdflib.Namespace(args.namespace[0])
        urls = args.url

        graph = LogsGraph.construct(catalog, *urls, spider=True)
        
        # maybe adding the index should be last, user is more prepared to 
        # answer questions about it
        newindex = LogSet.LogSet(ns+label)
        # newindex.add_to_graph()

        # known logseries to match against:
        todo = set([s for s in Logseries.logseries()])
        done = set()
        # files to catalog:
        baselen = len(topdir)+1
        remaining = set([ FileInfo(topdir, path[baselen:], f) 
                          for path, d, files in os.walk(path) for f in files ])

        # I think we need to ask the user at each logseries 
        # which subjects this series or dataset is about
        while len(todo) > 0:
            for logseries in todo:
                matching,remaining = logseries.candidates(remaining)
                for f in matching:
                    # I think newindex.add should do the finding-out-the-subject
                    newindex.add(f, logseries)
                done.add(logseries)
                todo.remove(logseries)
            



        todo = set([p for p in Logseries.known_filename_patterns()])
        done = set()

        while len(todo) > 0:
            for pattern in sorted(todo, key=len, reverse=True):
                logseries = LogSeries.find_logseries(pattern=pattern)
                matching = logseries.candidates(remaining):
                for f in matching:
                    log = ConcreteLog(f, logseries,...)
                    log.add_to_graph()
                remaining -= matching
                done.add(pattern)
                todo.remove(pattern)
            # next, with remaining files, find a suitable logseries (or define one)
            # .. and add it to todo then return to that loop
            # might sometimes need to defer/skip a file 

        newindex.add_to_graph()



if __name__ == '__main__':
    example = CatalogCommand.epilog() + 
              " -u file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples/nersc.ttl" +
              " -u file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples/cray-dict.ttl" +
    if len(sys.argv)==1:
        print(desc)
        sys.exit()

    parser = argparse.ArgumentParser(desc, epilog=example)
    parser.add_argument('-v','--verbose', action='count')
    parser.add_argument('-u', '--url', nargs=1, action='append')
    parser.set_defaults(func=help)
    subparsers = parser.add_subparsers()
    for cmd in CatalogCommand,FindCommand:
        cmd(subparsers)
    args = parser. parse_args()
    args.func(args)

