#!/usr/bin/env python3
""" read/write/manage the RDF/Turtle knowledge graph """

import logging
import sys
logging.debug(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

# example of a ConcreteLog:
#:console-20170907
#    a logset:ConcreteLog ;
#    logset:subject nersc:cori ;
#    dcat:downloadURL "p0-20170906t151820/console-20170907" ;
#    logset:isInstanceOf cray:console_logfile ;
#    dct:temporal [ a dct:PeriodOfTime ;
#                  logset:startDate "2017-09-07T00:00:37.627889-07:00"^^xsd:dateTime ;
#                  logset:endDate "2017-09-07T00:01:31.068610-07:00"^^xsd:dateTime ;
#                 ] ;
#    dcat:byteSize "5120"^^xsd:integer ;
#    .

import rdflib
from rdflib.term import URIRef, Literal, BNode
import LogsGraph
from LogClass import LogClass, BlankNode, PropertyInfo

class ConcreteLog(LogClass):
    """ object corresponding to a logset:ConcreteLog """

    rdf_class:str = 'logset:ConcreteLog'

    # each class should list/describe the properties it expects to have:
    # eg for LogSeries:
    #   property_info["logset:infoType"] = PropertyInfo(infotype,
    #                                       rdflib.term.URIRef, getinfotype)
    property_info = { 
        'logset:subject':      PropertyInfo('subject', URIRef, 'get_subject'),
        'logset:isInstanceOf': PropertyInfo('isInstanceOf', URIRef, 'abort'),
        'dcat:downloadURL':    PropertyInfo('downloadURL', URIRef, 'get_url'),
        'dcat:accessURL':      PropertyInfo('accessURL', URIRef, 'get_url'),
        'dct:temporal':        PropertyInfo('temporal', Temporal, 'inspect'),
        'dcat:byteSize':       PropertyInfo('byteSize', Literal, 'inspect'),
        'recordCount':         PropertyInfo('recordCount', Literal, 'inspect'),
        'estRecordCount':      PropertyInfo('estRecordCount', Literal, 'inspect')
                    }

    def _init(self):
        """ this is a hook for subclasses to override for initializing
            subclass-specific stuff that decouples them from __init__
            implementation
        """
        self._startDate = None
        self._endDate = None

#    @property
#    def startDate(self):
#        pass

    def get_subject(self, predicate:URIRef, context=None) -> List[URIRef]:
        print("{0} {1} called get_subject".format(self.__class__.__name__,str(self.uri)))
        return []

    def get_url(self, predicate:URIRef, context=None) -> List[URIRef]:
        print("{0} {1} called get_url".format(self.__class__.__name__,str(self.uri)))
        return []

    def inspect(self, predicate:URIRef, context=None) -> List:
        # call the appropriate handler (from logseries) to look at 
        # the file for time, size etc info
        # return a list of values for the appropriate predicate
        # should also update properties with those values (and others)
        print("{0} {1} called inspect".format(self.__class__.__name__,str(self.uri)))
        return []


class Temporal(BlankNode):

    rdf_class:str = 'dct:temporal'
    property_info = {
        # inspect will need to be called with context that includes the concretelog
        # so it can get the handlers
        'logset:startDate': PropertyInfo('startDate', Literal, 'inspect'),
        'logset:endDate': PropertyInfo('endDate', Literal, 'inspect')
                    }
