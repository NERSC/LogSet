#!/usr/bin/env python3
""" parse, call and test logset commands """

# system python 3 on Cori is broken so user will need to load a 
# python module, which will be 3.6+ anyway, so we'll take advantage
# of some of python's modern features:
import sys
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+")

import unittest
import logging
import argparse

from typing import Dict,Type,List

from abc import ABC, abstractmethod
class Command(ABC):
    parser = None

    @classmethod
    def setup_parser(cls, group: argparse._SubParsersAction) -> None:
        cls.parser = group.add_parser(cls.__name__.lower(), 
                                      help=cls.__doc__.split('\n',1)[0])

    @abstractmethod
    def run(self, args: argparse.Namespace=None):
        if args is None:
            self.args = self.parser.parse_args()
        else:
            self.args = args


_commands: Dict = None
def commands() -> Dict[str,Type[Command]]:
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

# -------------
def parse_args(cmdline: List[str]=sys.argv[1:], desc: str='') -> argparse.Namespace:
    logging.debug("parsing: " +str(cmdline))
    parser = argparse.ArgumentParser(description=desc)

    # arguments common to all subcommands:
    parser.add_argument('--vocab', help="path to vocab file", 
                        default='$LOGSET_ROOT/etc/vocab.ttl')
    parser.add_argument('-d', '--dict', help="location of logset.ttl vocab file",
                        default='./')
    parser.add_argument('-l', '--loglevel', default='WARNING', metavar='LEVEL',
                        choices=['debug','d','info','i','warning','w',
                                 'error','e','critical','c'], 
                        help="noisiness of log output: "+
                             "(D)EBUG,(I)NFO,(W)ARNING,(E)RROR,(C)RITICAL",
                        type=str.lower)

    # parsers for subcommands:
    subs = parser.add_subparsers(title="subcommands",metavar="COMMAND", dest='command')
    for name,cls in commands().items():
        cls.setup_parser(subs)

    if not cmdline:
         parser.print_help()
         return None 

    return parser.parse_args(cmdline)

class TestArgParsing(unittest.TestCase):
    def test_basic_help(self):
        try:
            args = parse_args('-h'.split())
        except SystemExit:
            pass # we're testing, so don't abort completely!
        # beyond eyeballing it, I don't know how to meaningfully
        # check that the captured output is sensible, so this is
        # mostly a placeholder:
        logging.debug('\nCaptured:\n'+capturedOutput.getvalue())
        assert True

    def test_set_vocab_file(self):
        assert False, "TODO test handling --vocab arg"

    def test_missing_vocab_file(self):
        assert False, "TODO test handling --vocab with wrong location"

    def test_set_dict_file(self):
        assert False, "TODO test handling --dict arg"

    def test_missing_dict_file(self):
        assert False, "TODO test handling --dict with wrong location"

# -------------
# when testing, redirect stdout (eg from argparse) to a stream:
capturedOutput = None
class Test(Command):
    """ Run unit tests """
    def run(self, args=None):
        super().run(args)

        # redirect stdout to a variable that we can capture and print/compare 
        # etc (thanks stackoverflow)
        import io
        global capturedOutput
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput   # redirect to capture

        import os
        root = os.path.realpath(__file__).rsplit('/',1)[0]
        testsuite = unittest.TestLoader().discover(root,pattern='*.py')
        unittest.TextTestRunner(verbosity=1).run(testsuite)

        sys.stdout = sys.__stdout__   # reset redirect
        logging.info("Testing captuerd the following stdout:\n"+capturedOutput.getvalue())


# -------------
class Help(Command):
    """ Print relevant help and exit """
    pass

class TestHelpCommand(unittest.TestCase):
    def test_help(self):
        assert False, "TODO create tests for Help command"


# -------------
class Create(Command):
    """ Create (with user guidance) an index.ttl for a set of log files """
    @classmethod
    def setup_parser(cls, group: argparse._SubParsersAction) -> None:
        super().setup_parser(group)
        cls.parser.add_argument('path', help="location to search for possible logfiles",
                            default='./')

    def run(self, args=None):
        super().run(args)
        

# -------------
class TestCreateCommand(unittest.TestCase):
    def setUp(self):
        self.cmd = Create()

    def test_parse_create_args(self):
        dummy_cmdline = 'create /path/to/some/logfiles'
        args = parse_args(dummy_cmdline.split())
        self.assertEqual(args.path, dummy_cmdline.split()[1])
    
    def test_create(self):
        assert False, "TODO create more tests for Create command"


# -------------
class Info(Command):
    """ Report on the contents and status of a logset """
    pass

class TestInfoCommand(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    #def test_show_vocab(self):

    def test_info(self):
        assert False, "TODO create more tests for Info command"


