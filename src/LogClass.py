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

from collections import namedtuple
# Each property that an RDF node expects to have should be described 
# by a class-level dict of predicate: Property
Property = namedtuple('Property', 'attribute, rdf_id_type, discover_method')
#  attribute is the object attribute for accessing it
#  rdf_id_type is rdflib.term.{URIRef,BNode,Literal}
#  discover_method is a method of the object, called with
#      this.discover_method(context)
#      that returns a value for this property (eg by asking 
#      questions of the user, or query the context for possible options, etc)
from Typing import Dict
PropertyDict = Dict[str, Property]

class LogClass:

    # what RDF class is this? (corresponds to "thing a class" in RDF)
    rdf_class:str = None # eg "logset:LogSet"

    # each class should list/describe the predicates it expects to 
    # have properties against:
    # eg for LogSeries:
    #   predicates = { "logset:infoType": Property(infotype, rdflib.term.URIRef, getinfotype }
    predicates: PropertyDict = {}


# --- FIXME: needs some rework to handle how predicates and properties are obtained ---

    # each class should define this map of predicate to attribute name (eg:
    #    "dct:title": "title"
    # what about things that need a blank node between, eg temporal?
    # or a named node, eg LogFormatType, which basically has mediatype and
    # is otherwise a tag for how logseries can be handled?
    # named node, the onject should have the named node, so looks after itself.
    # what about blank node?
    predicates: Dict[str,str] = { }

    # some properties are just held by the class for convenience (eg LogSeries
    # 
    #not_stored: List[str] = []

    def _init(self):
        """ this is a hook for subclasses to override for initializing
            subclass-specific stuff that decouples them from __init__ 
            implementation
        """
        pass

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

        # give subclasses a method to initialize private variables
        # to None, etc, without needing to replicate __init__
        self._init()

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
            # predicates we've defined are there for a reason: we generally want
            # graph to hold that information. So for each predicate we should also 
            # define an action for what to do before adding it to the graph if it 
            # is not set (eg "skip" or "select" or "ask" or "inherit")
            # some use cases:
            # - we need a title for a LogSet: ask the user for text. Show them
            #   a summary of things in it?
            #      (maybe we need to deinfe __str__ for each class, and print first
            #      10 lines of that)
            # - we need the subject for a concretelog. Some context of what created 
            #   the contextlog is prob useful here, otherwise maybe print a list of
            #   known Subjects? (inherit, search, select, create sequence here.. we 
            # want to get known subjects from the context (which would be the logset
            # creating it) .. and need a whole ui of asking the user to enter search 
            # terms (eg "cori" then show subjects in graph matching that)
            # basically 

            # on other hand, when creating/defining a logseries, we need to know about
            # the logformattpye (can do by inspect file type and if text, show user some records
            # and ask questions

            # its too class-specific, I think predicates needs to just define a
            # routine to call, maybe that takes a "context" argument (dict?),
            # that add_to_graph will call if attr is not set

            # to ask: we probably want to present the user with a list of options 
            # and let them select one or create a new one (eg, a title probably 
            # needs new text from the user, 
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
            # TODO don't forget literals! rdflib.term.Literal
            # all are rdflib.term.Identifier
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

