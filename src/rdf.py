#!/usr/bin/env python3
""" read/write/manage the RDF/Turtle knowledge graph """

# system python 3 on Cori is broken so user will need to load a 
# python module, which will be 3.6+ anyway, so we'll take advantage
# of some of python's modern features:
import sys
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+")

import rdflib
import logging

graph: rdflib.Graph = None

def parse_vocab(path=None):
    if path is None:
        import os
        root = os.path.realpath(__file__).rsplit('/',1)[0]
        path = '{0:s}/../etc/vocab.ttl'.format(root)
    
    global graph #, statements
    graph = rdflib.Graph().parse(path, format='turtle')
    #statements = graph.parse(path, format='turtle')


#
#import unittest
#class TestVocab(unittest.TestCase):
#
#    def test_can_parse_vocab(self):
#        parse_vocab()
#        
#        global statements
#        logging.debug("\nvocab has {0:d} statements:".format(len(statements)))
#        logging.debug("statements in native/internal format:")
#        # too much text, head-and-tail it:
#        def head_and_tail(lines):
#            logging.debug('\n'+'\n'.join(lines[:10]) + '\n ... \n' + '\n'.join(lines[-10:]))
#        head_and_tail([str(s) for s in statements])
#        logging.debug("\nregenerated turtle looks like:")
#        head_and_tail(statements.serialize(format='n3').decode('ascii').splitlines())
#        head_and_tail(statements.serialize(format='xml').decode('ascii').splitlines())
#        assert True
#
## for testing:
#if __name__ == '__main__':
#    logging.getLogger().setLevel(logging.DEBUG) 
#    unittest.main()
