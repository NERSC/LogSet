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

import rdflib
from rdflib.term import URIRef, BNode, Identifier

from collections import namedtuple
# Each property that an RDF node expects to have should be described 
# by a class-level dict of predicate: PropertyInfo
PropertyInfo = namedtuple('PropertyInfo', 'attribute, cls, discover_method')
#  - attribute is the object attribute for accessing it
#  - cls is either URIRef/Literal or a subclass of BlankNode
#  - when creating a triple, URIRefs and Literals can be used directly,
#    but when properties are encapsulated behind blank nodes, getting
#    the triples is delegated to a BlankNode LogClass 
#    (eg class Temporal(BlankNode)
#  - discover_method is a method of the object, called with
#      this.discover_method(predicate, context)
#    that returns a list of values for this property (eg by asking 
#    questions of the user, or query the context for possible 
#    options, etc)
#    discover_method can be skip, which returns an empty list, which
#    in turn prompts the class not to add this property to the graph
from Typing import Dict, List
PropertyInfoDict = Dict[str, PropertyInfo]
# the actual properties are in the form of predicate: list-of-values
PropertyValues   = List[Identifier]
PropertyDict     = Dict[str,PropertyValues]

from Typing import Tuple, Generator
Triple=Tuple[Identifier, Identifier, Identifier]

class LogClass:

    # what RDF class is this? (corresponds to "thing a class" in RDF)
    # note it is a string, we don't know the uri until the graph has 
    # been constructed
    rdf_class:str = None # eg "logset:LogSet"

    # each class should list/describe the properties it expects to have:
    # eg for LogSeries:
    #   property_info["logset:infoType"] = PropertyInfo(infotype, 
    #                                       URIRef, getinfotype)
    property_info: PropertyInfoDict = {}

    def _init(self):
        """ this is a hook for subclasses to override for initializing
            subclass-specific stuff that decouples them from __init__ 
            implementation
        """
        pass

    def __init__(self, uri:URIRef = None, 
                 namespace:rdflib.Namespace = None,
                 properties: PropertyDict = dict()): 
        """ if a uri is provided, namespace is ignored, otherwise a namespace
            must be provided to generate a unique uri in
        """    
        if uri is None:
            assert namespace is not None
            uri = namespace[ran_str(8)]
        self.uri = uri

        # give subclasses a method to initialize private variables
        # to None, etc, without needing to replicate __init__
        self._init()

        # properties is a dict of eg 
        #   "dct:title": Literal("my title")
        self.properties = {}
        for pred,values in properties.items():
            self.properties[pred] = values
        # all attributes named in property_info should have some value:
        for pred,info in self.property_info.items():
            values = self.properties.get(pred, [])
            setattr(self, info.attribute, values)

    # some common discover_methods:
    def skip(self, predicate:str, context=None):
        """ if it's not there, don't include it """
        return []

    def abort(self, predicate:str, context=None):
        """ if it's not there, something is badly wrong """
        msg = "{0} {1} missing predicate {2}".format(self.rdf_class, 
                                            str(self.uri), str(predicate))
        raise Exception(msg)


    def add_to_graph(self, context=None):
        for triple in self.triples(context):
            LogsGraph.graph.add( triple )


    def triples(self, context=None) -> Generator[:
        """ generator returning rdf triples (as tuples) that can be added to
            the graph to represent this item's properties (but not the item
            itself, which is handled directly by "add_to_graph" .. this allows
            recursion for blank nodes)
        """
        # first, describe me:
        rdf = LogsGraph.getns('rdf')
        ns,sep,rdf_class = self.rdf_class.partition(':')
        myclass = LogsGraph.getns(ns)[rdf_class]
        yield (self.uri, rdf.type, myclass)
        # then, my properties:
        for pred,values in self.properties.items():
            if len(values) == 0:
                if pred in self.property_info:
                    # make the subclass identify some values:
                    method = self.property_info[pred].discover_method
                    values += getattr(self,method)(pred, context)
            if len(values) == 0:
                continue
            # now make a triple for each:
            ns,sep,rdf_pred = pred.partition(':')
            predicate = LogsGraph.getns(ns)[rdf_pred]
            for v in values:
                if isinstance(v,BlankNode):
                    for t in  v.triples(context):
                        yield t
                else:
                    assert (isinstance(v, Identifier)
                    yield (self.uri, predicate, v)


class BlankNode(LogClass):
    # main difference between a BlankNode and other LogClass is that it is 
    # created in the graph as a BNode rather than a random string in the 
    # namespace
    # subclasses should still define predicates and properties

    def __init__(self, uri:URIRef = None, 
                 namespace:rdflib.Namespace = None,
                 properties: PropertyDict = dict()): 
        if uri is None:
            uri = BNode()
        super().__init__(uri,namespace,properties)


