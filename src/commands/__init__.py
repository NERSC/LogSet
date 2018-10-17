#!/usr/bin/env python3

import collections 
ArgDetails = collections.namedtuple('ArgDetails', 'short, long, nargs, required, help, example')

import logging

import sys
from abc import ABC
class Command(ABC):
    command = ""
    purpose = ""
    usage = ""
    _args = []
    def __init__(self, subparsers, parent):
        logging.debug("creating a {0} command".format(self.__class__.__name__)) 
        self.parser = subparsers.add_parser(self.command, help=self.usage, 
                                            epilog=self.epilog(), parents=[parent])
        for arg in self._args:
            self.parser.add_argument(arg.short, arg.long, nargs=arg.nargs, 
                                     required=arg.required, help=arg.help)
        self.parser.set_defaults(func=self.execute)

    @classmethod
    def epilog(cls):
        """ return some epilog help for this command """
        txt  = "{0} {1}".format(sys.argv[0], cls.command)
        for arg in cls._args:
            txt += ' {}'.format(arg.example)
        return txt

    def execute(self, args):
        print("executing {0} with args {1}".format(self.__class__.__name__, str(args)))

commands = []
__all__ = [ 'ArgDetails', 'Command', 'commands' ]

def _import_modules():
    # dynamically scan this directory for handler modules (plugin-style):
    # (borrowed and adapted from 
    # https://stackoverflow.com/questions/14426574/how-to-import-members-of-modules-within-a-package/14428820#14428820)
    # handler modules must set module variables for logFormat and constructor, eg:  
    #      logFormat = 'timeStampedLogfile'
    #      constructor = TimeStampedLogfile
    from importlib import import_module
    import os
    import inspect
    this = os.path.dirname(os.path.abspath(__file__))
    packagename = this.rpartition(os.sep)[2] 
    globals_ = globals()
    for filename in os.listdir(this):
        if filename[0] != '_' and filename.split('.')[-1] in ('py', 'pyw'):
            modulename = filename.split('.')[0]  # filename without extension
            m = import_module('.' + modulename, package=packagename)
            for name in m.__dict__:
                if not name.startswith('_'):
                    thing = m.__dict__[name]
                    if not inspect.ismodule(thing):
                        globals_[name] = thing
                        __all__.append(name)
                        if inspect.isclass(thing) and issubclass(thing,Command) and thing != Command:
                            print("found a {0} command to register in {1}".format(thing.__name__, filename))
                            commands.append(thing)

_import_modules()

