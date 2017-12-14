#!/usr/bin/env python3
""" parse, call and test logset commands """

import unittest

import argparse
from abc import ABC, abstractmethod
class Command(ABC):
    parser = None

    @classmethod
    def setup_parser(cls, group: argparse.Action) -> None:
        cls.parser = group.add_parser(cls.__name__.lower(), 
                                      help=cls.__doc__.split('\n',1)[0])

    @abstractmethod
    def run(self):
        pass


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
    def run(self):
        testsuite = unittest.TestLoader().discover('.',pattern='*.py')
        unittest.TextTestRunner(verbosity=1).run(testsuite)


class Help(Command):
    """ Print relevant help and exit """
    pass

class TestHelpCommand(unittest.TestCase):
    def test_something(self):
        assert False, "TODO create tests for Help command"


class Create(Command):
    """ Create (with user guidance) an index.ttl for a set of log files """
    pass

class TestCreateCommand(unittest.TestCase):
    def test_something(self):
        assert False, "TODO create tests for Create command"


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


