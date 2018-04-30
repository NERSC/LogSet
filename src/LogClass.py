#!/usr/bin/env python3
""" LogClass is a base for classes corresponding to owl:Classes in the 
    LogsGraph. The intent is to provide a common interface for instantiating
    things based on results of a query 
"""

import logging
import sys
logging.debug(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

import random, string
def ran_str(length: int) -> str:
    """ produce a string of random letters, of a given length.
        Used to generate uri if one was not provided
    """
    return ''.join([random.choice(string.ascii_lowercase) for i in range(length)])

from Typing import Dict
class LogClass:

    # what RDF class is this? (corresponds to "thing a class" in RDF)
    rdf_class:str = None # eg "logset:LogSet"

    # each class should define this map of predicate to attribute name (eg:
    #    "dct:title": "title"
    # what about things that need a blank node between, eg temporal?
    # or a named node, eg LogFormatType, which basically has mediatype and
    # is otherwise a tag for how logseries can be handled?
    # named node, the onject should have the named node, so looks after itself.
    # what about blank node?
    predicates: Dict[str,str] = { }

    def __init__(self, uri:str = None, properties: Dict = dict(), 
                 namespace: str = None):
        """ if a uri is provided, namespace is ignored, otherwise a namespace
            must be provided to generate a unique uri in
        """    
        if uri is None:
            assert namespace is not None
            if namespace[-1] != '#':
                namespace += '#'
            uri = namespace + ran_str(8)
        self.uri = uri

        # properties is a dict of eg "dct:title": "the title of this thing"
        # the predicates map maps it to an attribute:
        self.uri = uri
        for pred,attr in self.predicates.items():
            setattr(self, attr, properties.get(pred, None)
        self.properites = {}
        for p, v in properties.items():
            if p not in self.predicates:
                self.properties[p] = v

    def triples(self, uri):
        """ generator returning rdf triples (as tuples) that can be added to
            the graph to represent this item's properties (but not the item
            itself, which is handled directly by "add_to_graph" .. this allows
            recursion for blank nodes)
        """
        # my properties including those that are accessed as attributes:
        props = dict(self.properties)
        for pred,field in self.predicates.items():
            attr = getattr(self, field, None)
            if attr is not None:
                props[pred] = attr
        for pred, obj in props.items():
            p = rdflib.term.URIRef(pred)
            if type(obj) is BlankNode:
                # the bnode uri should be a string of a bnode id
                node = rdflib.term.BNode(obj.uri)
                # recurse into the bnode:`
                yield ( uri, p, node )
                for t in obj.triples():
                    yield t
                continue
            # in rdf, a subject can have many of the same predicate
            # each linking a different object. We'll handle those 
            # as lists
            elif type(attr) not in (list, tuple):
                attr = [attr]
                for a in attr:
                    obj = rdflib.term.URIRef(a)
                    yield (uri, p, obj)

    def add_to_graph(self):
        rdf = LogsGraph.getns('rdf')
        # first, describe me:
        uri = rdflib.term.URIRef(self.uri)
        myclass = rdflib.term.URIRef(self.rdf_class)
        LogsGraph.graph.add( (uri, rdf.type, myclass) )
        # then, my properties:
        for triple in self.triples(uri):
            LogsGraph.graph.add( triple )


class BlankNode(LogClass):
    # subclasses should still define predicates and properties

    def triples(self):
        uri = rdflib.term.BNode(self.uri)
        for t in super().triples(uri):
            yield t

