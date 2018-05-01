#!/usr/bin/env python3

import logging
import sys
logging.debug(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

# sample entry looks like:
#@prefix : <index#> .
#:
#    a logset:LogSet ;
#    dct:title "Sample NERSC logs" ;
#    rdfs:label "nersc-logs-001" ;   # is this necessary/useful?
#    dct:description "a partial sample of cori log data for testing logset tools"  ;
#    dct:publisher nersc:nersc ;
#    dcat:landingPage <file://cori.nersc.gov//global/cscratch1/sd/sleak/p0-20170906t151820/>
#    dct:contactPoint [ a vcard:Individual ;
#                       vcard:fn "Steve Leak" ;
#                       vcard:email "sleak@lbl.gov" ;
#                     ] ;
#    dcat:distribution
#        :console-20170906,
#        :console-20170907,
#        :consumer-20170906,
#        :consumer-20170907,
#        :messages-20170906,
#        :messages-20170907 ;
#    .

import rdflib
import LogsGraph

from LogClass import LogClass
class LogSet(LogClass):

    rdf_class = "logset:LogSet"

    # each class should define this map of predicate to attribute name (eg:
    #    "dct:title": "title"
    predicates = { "dct:title":         'title',        # string
                   "dct:description":   'description',  # string
                   "dct:publisher":     'publisher',    # uri (foaf:Agent)
                   "dct:contactPoint":  'contactpoint', # uri or blank node (vcard)
                   "dcat:landingPage":  'landingpage',  # uri
                   "dcat:distribution": 'concretelogs'  # list of uris
                 }

    def _init(self):
        pass

    def add(self, fileinfo: FileInfo, logseries: LogSeries, subject: Subject):
#        # make a concretelog and add it to the graph
#        # what properties do we know?
#        props = {}
#        props["logset:isInstanceOf"] = logseries.uri
#        # need temporal (blank node) and subject
#        # temporal comes from inspecting the log
#        # subject .. might come from inspecting the log?
#        concretelog = ConcreteLog(namespace=self.namespace)
#        concretelog.inspect()
#        concretelog.add_to_graph()


#class LogSet:
#
#    # dict mapping object attributes to RDF predicates:
#    # TODO might need utility classes to handle rdf uris?
#    attributes = { 'title':        'dct:title',          # rdf literal string
#                   'description':  'dct:description',    # rdf literal string
#                   'publisher':    'dct:publisher',      # rdf uri (foaf:agent)
#                   'contactPiont': 'dct:contactPoint',   # rdf uri (vcard:kind)
#                   'distribution': 'dcat:distribution' } # rdf uri
#
#    # FIXME: dcat:landingpage, for eg, isn't a valid key in properties,
#    # but a LogSet might be created with such things. How to best 
#    # handle that?
#    def __init__(self, uri: str, **properties: rdflib.term.Identifier): 
#        """ eg: uri = http://example.org/myindex#myindex
#            corresponds to a file like http://example.org/myindex.ttl
#            with: 
#                @prefix myindex: http://example.org/myindex#
#                myindex:myindex
#                    a logset:LogSet ;
#                    rdfs:label "myindex" ;
#                    dcat:distribution myindex:concrete-file-1 .
#                myindex:concrete-file-1
#                    a logset:ConcreteLog ;
#            **properties allows a LogSet to be instantiated from a sparql query
#        """
#        self.uri = uri
#        ns,sep,label = uri.rpartition('#')
#        self.namespace = rdflib.Namespace(ns+sep)
#        if label == '':
#            label = ran_str(8)
#        self.label = label
#        self.prefix = label
#
#        well_known_properties = set(self.attributes.keys())
#        provided_properties = set(properties.keys())
#        for p in well_known_properties & provided_properties:
#            setattr(self, p, properties[p])
#        remaining = provided_properties - well_known_properties
#        self.other_properties = { p: properties[p] for p in remaining }
#
#    # how do we get the subject? either it comes from user (passed through),
#    # or it can be inferred from the log itself, either via the filepattern
#    # (from the logseries) or by inspecting the log
#    # this goes for specificSubjectPattern too
#    def add(self, fileinfo: FileInfo, logseries: LogSeries, subject: Subject):
#        # make a concretelog and add it to the graph
#        # what properties do we know?
#        props = {}
#        props["logset:isInstanceOf"] = logseries.uri
#        # need temporal (blank node) and subject
#        # temporal comes from inspecting the log
#        # subject .. might come from inspecting the log?
#        concretelog = ConcreteLog(namespace=self.namespace)
#        concretelog.inspect()
#        concretelog.add_to_graph()
#

#    def triples(self):
#        """ generate a set of RDF triples describing this LogSet """
#        # FIXME ugh this is kinda clumsy:
#        nspaces = getattr(self, _namespaces, None):
#        if nspaces is None:
#            nspaces = {}
#            for attr in self.attributes:
#                prefix,sep,item = attr.partition(':')
#                if prefix not in nspaces:
#                    nspaces[prefix] = LogsGraph.getns(prefix)
#            #for prefix in ('rdf','rdfs','logset'):
#            #     nspaces[prefix] = LogsGraph.getns(prefix)
#            self._namespaces = nspaces
#
#        rdf = LogsGraph.getns('rdf')
#        rdfs = LogsGraph.getns('rdfs')
#        logset = LogsGraph.getns('logset')
#        yield (self.uri, rdf.type, logset.LogSet)
#        yield (self.uri, rdfs.label, rdflib.Literal(self.label))
#        # FIXME ugh is value sane? what abount self.other_properties?
#        for attr in self.attributes:
#            value = getattr(self,attr,None) or continue
#            prefix,sep,item =attr.partition(':')
#            ns = nspaces[prefix]
#            yield (self.uri, ns[item], value)  
#
#
#    # some derived attributes:
#    @property
#    def startDate(self):
#        # find and return earliest startDate in concrete logs
#        return None # TODO
#
#    @property
#    def endDate(self):
#        # find and return latest endDate in concrete logs
#        return None # TODO
#
#    def subjects(self):
#        # iterate over set of subjects described by concrete logs
#        pass
#
#    import UI
#    def define(self, **kwargs):
#        # using current attributes and any passed kwargs as a starting
#        # point, fill out the essential properties of this logset
#        
#        pass 



# sparql query like:
#  select ?title ?description ?publisher ?contactname ?contactemail where {
#    ?logset a logset:LogSet .
#    ?logset dct:title ?title .
#    ?logset dct:description ?description .
#    optional { ?logset dct:contactPoint/vcard:fn ?contactname } .
#    optional { ?logset dct:contactPoint/vcard:email ?contactemail } .
#?id dct:temporal/logset:startDate ?start .
#



        
