#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

# a sample subject looks like:
#:nersc_crt
#    a logset:Subject ;
#    rdfs:label "nersc" ;
#    skos:note "nersc the facility (as distinct from NERSC the organization)" ;
#    .
#
#:cori
#    a logset:Subject ;
#    rdfs:label "cori" ;
#    logset:isSpecific ddict:cluster ;
#    dct:description "cori is the 12000-node Cray XC40 at NERSC" ;
#    dcat:landingPage <http://www.nersc.gov/systems/cori/> ;
#    .

from Node import Node
from graph import localdict_ns, entities_ns

# forward declaration .. will this work?
class SubjectType:
    pass

class SubjectType(Node):
    rdf_class = "logset:SubjectType"
    getters = {
        'skos:prefLabel': 'ask',
        'skos:note': 'ask',
        'logset:aspectOf': 'multi_select',
        'skos:broader': 'multi_select',
        'skos:narrower': 'multi_select',
              }
    required_properties = set(['skos:prefLabel'])
    prompts = {
        'skos:prefLabel':  "A short label for {0}? ",
        'skos:note':       "An optional clarifying note for {0}? ",
        'logset:aspectOf': "What is {0} an aspect of? (ie part of) ",
        'skos:broader':    "Is {0} a more general form of something (eg server comapred to node)? ",
        'skos:narrower':   "Is {0} a more specific instance of another subject (eg hsn compared to network)? "
              }
    targets = {
        'logset:aspectOf': SubjectType,
        'skos:broader':    SubjectType,
        'skos:narrower':   SubjectType
                }

#    finder_query = ''' SELECT ?uri (SAMPLE(?label) as ?label)
#                                   (SAMPLE(?note) as ?note)  WHERE {
#                          ?uri a logset:SubjectType .
#                          ?uri skos:prefLabel ?label .
#                          OPTIONAL { 
#                            ?uri skos:note ?note .
#                          }
#                        } GROUP BY ?uri
#                   '''
#    finder_fields = [ 'uri', 'skos:prefLabel', 'skos:note' ]
    label_property:str = 'skos:prefLabel'
    label_alternate:str = 'type of subject'

    @property
    def uri(self):
        # lazily find uri so there is a chance of deriving a readable one from foaf:name
        if self._uri is None:
            ns = self._namespace or localdict_ns()
            self._uri = self.make_uri(self.label_property, ns)
        return self._uri

# forward declaration so we can set Subject as targets:
class Subject:
    pass

class Subject(Node):
    rdf_class = "logset:Subject"
    getters = {
        'rdfs:label': 'ask', 
        'dct:description': 'ask',
        'dcat:landingPage': 'ask',
        'logset:isSpecific': 'select',
        'logset:partOf': 'select',
        'logset:affects': 'multi_select' 
              }
    required_properties = set(['rdfs:label', 'dct:description', 'logset:isSpecific'])
    prompts = {
        'rdfs:label':        "A short identifying label for {0}: ",
        'dct:description':   "Please describe {0}: ",
        'dcat:landingPage':  "A URL with more information about {0}? (may be blank) ",
        'logset:isSpecific': "What type of thing is {0}? ",
        'logset:partOf':     "What is {0} most directly part of? ",
        'logset:affects':    "What other things do issues in {0} affect? "
              }
    targets = {
        'logset:isSpecific': SubjectType,
        'logset:partOf':     Subject,
        'logset:affects':    Subject,
        # kinda-ugly hack: when cataloging a logset it is helpful to have a 
        # high-level list of subjects to infer more specific subjects for each
        # logseries. So, the catalog command creates a dummy Subject
        'logset:subject':    Subject
                }
#    finder_query = ''' SELECT ?uri (SAMPLE(?label) as ?label)
#                                   (SAMPLE(?description) as ?description)
#                                   (SAMPLE(?type) as ?type)
#                                   (SAMPLE(?page) as ?page)  WHERE {
#                          ?uri a logset:Subject .
#                          ?uri rdfs:label ?label .
#                          ?uri dct:description ?description .
#                          ?uri logset:isSpecific ?type .
#                          OPTIONAL { 
#                            ?uri dcat:landingPage ?page .
#                          }
#                        } GROUP BY ?uri
#                   '''
#    finder_fields = [ 'uri', 'rdfs:label', 'dct:description', 
#                      'logset:isSpecific', 'dcat:landingPage' ]
    label_property:str = 'rdfs:label'
    label_alternate:str = 'type of subject'

    @property
    def uri(self):
        # lazily find uri so there is a chance of deriving a readable one from foaf:name
        if self._uri is None:
            ns = self._namespace or entities_ns()
            self._uri = self.make_uri(self.label_property, ns)
        return self._uri

