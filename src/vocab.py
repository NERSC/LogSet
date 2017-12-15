#!/usr/bin/env python3
""" read and write RDF/Turtle descriptions of things """

import rdflib
import logging

graph = None
statements = None

def parse_vocab(path=None):
    if path is None:
        import os
        root = os.path.realpath(__file__).rsplit('/',1)[0]
        path = '{0:s}/../etc/vocab.ttl'.format(root)
    
    global vocab, statements
    vocab = rdflib.Graph()
    statements = vocab.parse(path, format='turtle')


import unittest
class TestVocab(unittest.TestCase):

    def test_can_parse_vocab(self):
        parse_vocab()
        
        import io
        import sys
        capturedOutput = io.StringIO()
        sys.stdout = capturedOutput   # redirect to capture
        
        global statements
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

