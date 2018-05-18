#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
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

from util import UI, Context, MultiDict, ran_str
from Node import Node
from graph import entities_ns, set_ns_base, the_graph
import rdflib
from rdflib.term import URIRef, BNode

class Agent(Node):
    rdf_class = "foaf:Organization"
    rdf_superclass = "foaf:Agent"
    getters = {
        'foaf:name': 'ask', 
        'foaf:page': 'ask' 
              }
    required_properties = set(['foaf:name'])
    prompts = {
        'foaf:name': "Name of {0}? (generally an organization) ",
        'foaf:page': "URL with more information about {0}? "
              }
#    finder_query = ''' SELECT ?uri (SAMPLE(?name) as ?name) (SAMPLE(?page) as ?page) WHERE {
#                          ?uri a ?type .
#                          ?type rdfs:subClassOf* foaf:Agent . 
#                          ?uri foaf:name ?name .
#                          OPTIONAL {
#                            ?uri foaf:page ?page .
#                          }
#                        } GROUP BY ?uri
#                   '''
#    finder_fields = [ 'uri', 'foaf:name', 'foaf:page' ]
    label_property:str = 'foaf:name'
    label_alternate:str = 'the publisher'

#    @property
#    def label(self):
#    #def label(self, context:Context=None) -> str:
#        #return self._properties.one(self.label_property) or 'the publisher'
#        return self.get_one_value(self.label_property) or 'the publisher'

    @property
    def uri(self):
        # lazily find uri so there is a chance of deriving a readable one from foaf:name
        if self._uri is None:
            ns = self._namespace or entities_ns()
            self._uri = self.make_uri(self.label_property, ns)
        return self._uri


class Vcard(Node):
    rdf_class = "vcard:Individual"
    # FIXME I'm not reading in the vcard graph properly for some reason,
    # so the link between Kind and Individual isn't being found. Sidestep it
    # for now:
    #rdf_superclass = "vcard:Kind"
    getters = {
        'vcard:fn':    'ask', 
        'vcard:email': 'ask'
              }
    required_properties = set(getters.keys())
    prompts = {
        'vcard:fn':    "Full name of {0}? ",
        'vcard:email': "Email address for {0}? "
              }
    finder_query = ''' SELECT ?uri (SAMPLE(?name) as ?name) (SAMPLE(?email) as ?email) WHERE {
                          ?uri a ?type .
                          ?type rdfs:subClassOf* vcard:Kind . 
                          ?uri vcard:fn ?name .
                          OPTIONAL {
                            ?uri vcard:email ?email .
                          }
                        } GROUP BY ?uri
                   '''
    finder_fields = [ 'uri', 'vcard:fn', 'vcard:email' ]
    label_property:str = 'vcard:fn'
    label_alternate:str = 'contact person'

#    #@property
#    #def label(self):
#    def label(self, context:Context=None) -> str:
#        #return self._properties.one(self.label_property) or 'contact person'
#        return self.get_one_value(self.label_property) or 'contact person'

    @property
    def uri(self):
        # lazily find uri so there is a chance of deriving a readable one from the label
        if self._uri is None:
            ns = self._namespace or entities_ns()
            self._uri = self.make_uri(self.label_property, ns)
        return self._uri



class LogSet(Node):

    rdf_class = "logset:LogSet"

    getters = {
        'dct:title':         'ask',
        'dct:description':   'ask',
        'dct:publisher':     'select',
        'dct:contactPoint':  'select',
        'logset:isClosed':   'truefalse',
        'dcat:landingPage':  'ask',
        'dcat:distribution': 'skip'
              }
    required_properties = set(['dct:title'])

    targets = {
        'dct:publisher':     Agent,
        'dct:contactPoint':  Vcard
                }

    # prompts for simple questions system can "ask" to get some properties:
    prompts = {
        'dct:title':       "Give {0} a title (eg \"Cori smw logs p0-20170906t151820\"): ",
        'dct:description': "Please enter short description of {0}: ",
        'dcat:landingPage': "URL for information about or access to {0}? (may be blank) ",
        'dct:publisher':    "Which organization is the publisher for {0}?",
        'dct:contactPoint': "Who is the contact person for {0}?",
        'logset:isClosed':  "is this a closed (ie no new data will arrive) dataset? "              }
    label_property:str = 'dct:title'
    label_alternate:str = 'this log set'

    def __init__(self, uri:URIRef, 
                 properties:MultiDict = None) -> None: 
        super().__init__(properties)
        uri_str = str(uri)
        if '#' not in uri_str:
            raise Exception("LogSet requires a URI in the form 'namespace#label'")
        cut = uri_str.rfind('#')+1
        
        self._uri = uri
        self.prefix = uri_str[cut:]
        self.namespace = rdflib.Namespace(uri_str[:cut])
        self.graph.bind(self.prefix, self.namespace)
        #the_graph.bind(self.prefix, self.namespace)

        # set a base for where new entities or local dict can be placed:
        cut2 = uri_str[:cut].rfind('/')
        set_ns_base(uri_str[:cut2])


    @property
    def label(self):
    #def label(self, context:Context=None) -> str:
        #title = self._properties.one('dct:title') or ''
        title = self.get_one_value('dct:title') or ''
        if title: 
            # put the title in quotes, if there is one:
            return "this log set \"{0}\"".format(title)
        else:
            return "this log set"

