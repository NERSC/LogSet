#!/usr/bin/env python3
""" read and write RDF/Turtle descriptions of things """

import rdflib

import logging
#log = logging.getLogger(__name__)
import unittest
class TestVocab(unittest.TestCase):

    def setUp(self):
        self.vocab_graph = rdflib.Graph()

    def test_can_parse_vocab(self):
        import os
        vocab_path = os.getcwd() + '/samples/vocab.ttl'
        statements = self.vocab_graph.parse(vocab_path, format='turtle')
        
        import io
        import sys
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput   # redirect to capture
        
        print("\nvocab has {0:d} statements:".format(len(statements)))
        for s in statements:
            print(s)
        print("\nregenerated turtle looks like:")
        print(statements.serialize(format='n3').decode('ascii'))
        print(statements.serialize(format='xml').decode('ascii'))

        sys.stdout = sys.__stdout__   # reset redirect

        # not having a convenient automatic test for "this is sane", 
        # dump it to the log for now:
        logging.debug('\nCaptured:\n'+capturedOutput.getvalue())
        assert True

