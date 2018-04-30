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
#    .

import rdflib
import LogsGraph

class ConcreteLog:
    """ object corresponding to a logset:ConcreteLog """

    # probably should get the accessor via the logseries

    def __init__(self, uri: str):
        self.uri = uri
        #self.name = uri.rpartition('#')[2]
        #self._fmtinfo = None # dict of key: list-of-values
        #self._filepatterns = None # set() of regex strings


