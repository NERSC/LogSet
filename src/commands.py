#!/usr/bin/env python3
""" parse, call and test logset commands """

import unittest
import logging
import argparse

from abc import ABC, abstractmethod
class Command(ABC):
    parser = None

    @classmethod
    def setup_parser(cls, group: argparse.Action) -> None:
        cls.parser = group.add_parser(cls.__name__.lower(), 
                                      help=cls.__doc__.split('\n',1)[0])

    @abstractmethod
    def run(self, args=None):
#        if args is None:
#            logging.debug("hello?")
#            self.args = self.parser.parse_args()
#            logging.debug("hello?")
#        else:
            self.args = args


_commands= None
# type checking requires python3.5+, too new for Cori system python:
#from typing import Dict,Type
#def commands() -> Dict[str,Type[Command]]:
def commands():
    """ return a list of (name,class) tuples for supported commands """
    global _commands
    if _commands is None:
        import inspect
        import sys
        def isUserCmd(cls): 
            return (inspect.isclass(cls) and cls.__module__ == __name__ 
                    and cls is not Command and not issubclass(cls, unittest.TestCase))
        _commands = {}
        for name,cls in inspect.getmembers(sys.modules[__name__], isUserCmd):
            _commands[name.lower()] = cls
    return _commands


class Test(Command):
    """ Run unit tests """
    def run(self, args=None):
        super().run()
        import os
        root = os.path.realpath(__file__).rsplit('/',1)[0]
        testsuite = unittest.TestLoader().discover(root,pattern='*.py')
        unittest.TextTestRunner(verbosity=1).run(testsuite)


class Help(Command):
    """ Print relevant help and exit """
    pass

class TestHelpCommand(unittest.TestCase):
    def test_something(self):
        assert False, "TODO create tests for Help command"


class Create(Command):
    """ Create (with user guidance) an index.ttl for a set of log files """
    def __init__(self):
        self.parser.add_argument('path', help="location to search for possible logfiles",
                            default='./')

    def run(self, args=None):
        super().run()
        

class TestCreateCommand(unittest.TestCase):
    def setUp(self):
        self.cmd = Create()

    def test_parse_create_args(self):
        dummy_arg = '/path/to/some/logfiles'
        self.parser.parse_args(dummy_arg.split())


        # capturing stdout from help, (thanks stackoverflow)
        import io
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput   # redirect to capture
        try:
            parse_args('-h'.split())
        except SystemExit:
            pass # we're testing, so don't abort completely!
        sys.stdout = sys.__stdout__   # reset redirect
        # beyond eyeballing it, I don't know how to meaningfully
        # check that the captured output is sensible, so this is
        # mostly a placeholder:
        logging.debug('\nCaptured:\n'+capturedOutput.getvalue())
        assert True
    
    def test_something(self):
        assert False, "TODO create more tests for Create command"


class Info(Command):
    """ Report on the contents and status of a logset """
    pass

class TestInfoCommand(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    #def test_show_vocab(self):

    def test_something_else(self):
        assert False, "TODO create more tests for Info command"


