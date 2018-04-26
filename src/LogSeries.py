#!/usr/bin/env python3

import sys
print(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+ .. try:\n  module load python/3.6-anaconda-4.4")

import rdflib

# utilities needed to identify the appropriate logseries given a 
# file pattern:
_pattern_tag_regexs = {}    # tag: regex_pattern
_logseries_for_pattern = {} # pattern (str): LogSeries
def 

def known_filename_patterns(graph: graph: rdflib.Graph):
    """ iterate over """
    query = '''SELECT ?tag ?regex WHERE {
                ?id a logset:FilenamePattern .
                ?id logset:tag ?tag .
                ?id logset:regex ?regex .
            }'''
    global _filenamepatterns
    for row in graph.query(query):
        _filenamepatterns[str(row[0])] = str(row[1])

_logseries = {} # label: LogSeries
def 


from typing import Pattern
import re
def logseries_for_filename_pattern(pattern: Pattern):
    """ return the logseries associated with a filename pattern """

class LogSeries:
    """ object corresponding to a logset:LogSeries """

    # rdf predicates corresponding to object attributes:
    _predicates = {'logset:infoType': 'infoTypes',
    _predicates = {'logset:infoType': 'infoTypes',
                   

    def __init__(self, graph: rdflib.Graph, uri: str = None, 
                 namespace: str = None, label: str = None,
                 **properties: rdflib.Term.Identifier): 
        """ a LogSeries is either in a graph, or needs to be described and 
            added to one
        """
        self._graph = graph
        if uri is None:
            if namespace is None:
                raise Exception("need either a uri, or a namespace and optional label") 
            

        self.uri = uri
        ns,sep,label = uri.rpartition('#')
        self.namespace = rdflib.Namespace(ns+sep)
        if label == '':
            label = ran_str(8)
        self.label = label
        self.prefix = label

    def candidates(self, 

    
:messages_logfile
    a logset:LogSeries ;
    logset:infoType dict:log_messages ;
    logset:logFormatType dict:timeStampedLogFile ;
    logset:logFormatInfo "filepattern=messages-<date:YYYYMMDD>$" ;
    logset:logFormatInfo "filepattern=messages$" ;
    logset:logFormatInfo "ts_words=1" ;
    logset:logFormatInfo "part_word=2" ;
