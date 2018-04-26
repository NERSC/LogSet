#!/usr/bin/env python3

import sys
print(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+ .. try:\n  module load python/3.6-anaconda-4.4")

# each new ConcreteLog in the LogSet needs a unique iri:
import random, string
def ran_str(length: int) -> str:
    " produce a string of random letters, of a given length "
    return ''.join([random.choice(string.ascii_lowercase) for i in range(length)])

@prefix : <index#> .
:
    a logset:LogSet ;
    logset:subject nersc:cori ;
    dct:title "Sample NERSC logs" ;
    rdfs:label "nersc-logs-001" ;   # is this necessary/useful?
    dct:description "a partial sample of cori log data for testing logset tools"  ;
    dct:publisher nersc:nersc ;
    dct:contactPoint [ a vcard:Individual ;
                       vcard:fn "Steve Leak" ;
                       vcard:email "sleak@lbl.gov" ;
                     ] ;
    dct:temporal [ a dct:PeriodOfTime ;
                  logset:startDate "2017-09-06T15:18:20.827169-07:00"^^xsd:dateTime ;
                  logset:endDate "2017-09-07T15:22:42.809617-07:00"^^xsd:dateTime ;
                 ] ;
    dcat:distribution
        :console-20170906,
        :console-20170907,
        :consumer-20170906,
        :consumer-20170907,
        :messages-20170906,
        :messages-20170907 ;
    .

import rdflib
import LogsGraph
class LogSet:

    # dict mapping object attributes to RDF predicates:
    # TODO might need utility classes to handle rdf uris?
    attributes = { 'title':        'dct:title',          # rdf literal string
                   'description':  'dct:description',    # rdf literal string
                   'publisher':    'dct:publisher',      # rdf uri (foaf:agent)
                   'contactPiont': 'dct:contactPoint',   # rdf uri (vcard:kind)
                   'distribution': 'dcat:distribution' } # rdf uri

    def __init__(self, uri: str, **properties: rdflib.Term.Identifier): 
        """ eg: uri = http://example.org/myindex#myindex
            corresponds to a file like http://example.org/myindex.ttl
            with: 
                @prefix myindex: http://example.org/myindex#
                myindex:myindex
                    a logset:LogSet ;
                    rdfs:label "myindex" ;
                    dcat:distribution myindex:concrete-file-1 .
                myindex:concrete-file-1
                    a logset:ConcreteLog ;
            **properties allows a LogSet to be instantiated from a sparql query
        """
        self.uri = uri
        ns,sep,label = uri.rpartition('#')
        self.namespace = rdflib.Namespace(ns+sep)
        if label == '':
            label = ran_str(8)
        self.label = label
        self.prefix = label

        well_known_properties = set(self.attributes.keys())
        provided_properties = set(properties.keys())
        for p in well_known_properties & provided_properties:
            setattr(self, p, properties[p])
        remaining = provided_properties - well_known_properties
        self.other_properties = { p: properties[p] for p in remaining }

    def triples(self):
        """ generate a set of RDF triples describing this LogSet """
        # FIXME ugh this is kinda clumsy:
        nspaces = getattr(self, _namespaces, None):
        if nspaces is None:
            nspaces = {}
            for attr in self.attributes:
                prefix,sep,item = attr.partition(':')
                if prefix not in nspaces:
                    nspaces[prefix] = LogsGraph.getns(prefix)
            #for prefix in ('rdf','rdfs','logset'):
            #     nspaces[prefix] = LogsGraph.getns(prefix)
            self._namespaces = nspaces

        rdf = LogsGraph.getns('rdf')
        rdfs = LogsGraph.getns('rdfs')
        logset = LogsGraph.getns('logset')
        yield (self.uri, rdf.type, logset.LogSet)
        yield (self.uri, rdfs.label, rdflib.Literal(self.label))
        # FIXME ugh is value sane? what abount self.other_properties?
        for attr in self.attributes:
            value = getattr(self,attr,None) or continue
            prefix,sep,item =attr.partition(':')
            ns = nspaces[prefix]
            yield (self.uri, ns[item], value)  


    # some derived attributes:
    @property
    def startDate(self):
        # find and return earliest startDate in concrete logs
        return None # TODO

    @property
    def endDate(self):
        # find and return latest endDate in concrete logs
        return None # TODO

    def subjects(self):
        # iterate over set of subjects described by concrete logs
        pass

    import UI
    def define(self, **kwargs):
        # using current attributes and any passed kwargs as a starting
        # point, fill out the essential properties of this logset
        
        pass 



# sparql query like:
#  select ?title ?description ?publisher ?contactname ?contactemail where {
#    ?logset a logset:LogSet .
#    ?logset dct:title ?title .
#    ?logset dct:description ?description .
#    optional { ?logset dct:contactPoint/vcard:fn ?contactname } .
#    optional { ?logset dct:contactPoint/vcard:email ?contactemail } .
#?id dct:temporal/logset:startDate ?start .
#



        
