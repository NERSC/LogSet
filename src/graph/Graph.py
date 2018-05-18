#!/usr/bin/env python3
""" read/write/manage the RDF/Turtle knowledge graph """

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

import rdflib
import urllib

the_graph: rdflib.ConjunctiveGraph = None

# location of the single-source-of-truth ontology and basic data dictionary:
base = 'http://portal.nersc.gov/project/mpccc/sleak/resilience/datasets/'


# when constructing or extending a graph the new rdf/ttl file might invoke 
# still more new namespaces, so we take an iterative 2-phase approach of 
# collecting urls to prase, and parsing them:
from typing import Set
_parsed: Set[str] = set()
_unparsed: Set[str] = set()

# rdflib defines a bunch of namespaces, I want them to be available via 
# lowercase prefixes / getns, but I don't want them automatically polluting 
# a subgraph I'm intending to write to a file. So, keep track of the 
# but not explicitly defined in a subgraph (because that 
# is mostly for writing out indexes etc)
_predefined_prefixes = {
  'rdf': rdflib.namespace.RDF,
  'rdfs': rdflib.namespace.RDFS,
  'owl': rdflib.namespace.OWL,
  'xsd': rdflib.namespace.XSD,
  'foaf': rdflib.namespace.FOAF,
  'skos': rdflib.namespace.SKOS,
  'doap': rdflib.namespace.DOAP,
  'dc': rdflib.namespace.DC,
  'dct': rdflib.namespace.DCTERMS
}

#      'vcard':  'https://www.w3.org/2006/vcard/ns',
_preferred_prefixes = {
      'dcat':   'http://www.w3.org/ns/dcat#',
      'vcard':  'https://www.w3.org/2006/vcard/ns',
      'logset': base+'logset#',
      'ddict':  base+'ddict#'
}

#_added_prefixes = {}

# rdf namespace manager binding is a little flaky, so we'll coerce it in a few 
# places .. pull that functionality into a routine:
def _bind_namespaces(g: rdflib.ConjunctiveGraph) -> None:
    # bind well-known namespaces to well-known prefixes:
    # note: graph.bind has a bug, doesn't clear existing prefixes
    # so the end result is a bit of a mess. So we'll use the 
    # namespace_manager to do it:
    for pref, ns in _predefined_prefixes.items():
        g.namespace_manager.bind(pref, ns, replace=True, override=True)
    # and we bind our preferred ones last, to hopefully clear junk:
    for pref, ns in _preferred_prefixes.items():
        logging.debug("rebinding: {0} to {1}".format(pref, str(ns)))
        g.namespace_manager.bind(pref, ns, replace=True, override=True)
#    for pref, ns in _added_prefixes.items():
#        g.namespace_manager.bind(pref, ns, replace=True, override=True)


# if a user needs to describe new subjects, or logseries, or contact points
# etc, these should be written somewhere (initally just to files that the user 
# can merge or publish) .. but they should also have a namespace, so 
# we'll define ones called 'localdict' and 'entities':
_ns_base = None
_localdict = None
_entities = None
def set_ns_base(base_uri):
    """ normally LogSet would call this .. """ 
    global _ns_base, _localdict, _entities
    _ns_base = base_uri
    # reset these too:
    #_localdict = None
    #_entities = None

from util import UI
def entities_ns():
    global _entities
    if _entities is None:
        prompt = "What namespace should newly-added entities have? "
        guess = _ns_base + '/entities#'
        response = UI.ask(prompt, guess)
        _entities = rdflib.Namespace(response)
        _preferred_prefixes['new_entities'] = response
        # FIXME: this is a bit clumsy, where *should* it be happening?
        _bind_namespaces(the_graph)
    return _entities

def localdict_ns():
    global _localdict
    if _localdict is None:
        prompt = "What namespace should data dictionary additions have? "
        guess = _ns_base + '/localdict#'
        response = UI.ask(prompt, guess)
        _localdict = rdflib.Namespace(response)
        _preferred_prefixes['localdict'] = response
        # FIXME: this is a bit clumsy, where *should* it be happening?
        _bind_namespaces(the_graph)
    return _localdict

import os
def construct(*catalog_urls: str, spider=False) -> rdflib.ConjunctiveGraph:
    """ starting with one or more catalog urls, parse the catalogs
        and optionally any peers, then build out the graph by fetching
        and reading all of the datasets.
        Note that this will clear and replace an existing graph.
    """
    global the_graph, _parsed, _unparsed
    the_graph = rdflib.ConjunctiveGraph()

    _unparsed = set([base+'logset#', base+'ddict#'])
    _parsed = set()

    # for some queries we need foaf in the graph too:
    _unparsed.add(rdflib.namespace.FOAF.rstrip('#')) # + 'index.rdf')
    
    extend(*catalog_urls, spider=spider)
    _bind_namespaces(the_graph)

    # as a sanity check:
    with open("whole_graph.ttl", 'w') as f:
            f.write(the_graph.serialize(format='n3').decode('ascii'))

    return the_graph

def extend(*new_urls: str, spider=False) -> rdflib.ConjunctiveGraph:
    """ extend the graph with the currently-unparsed urls """
    global the_graph, _parsed, _unparsed
    q_remotes = ''' SELECT ?uri WHERE
                    { ?cat a dcat:Catalog .
                       ?cat rdfs:seeAlso ?uri . } '''
    q_logsets = '''SELECT ?uri WHERE 
                     { ?cat a dcat:Catalog .
                       ?cat dcat:dataset ?uri . }'''

    logging.info("extending the_graph with: {0}".format(str(new_urls)))
    for url in new_urls:
        if url not in _parsed:
            _unparsed.add(url)
    logging.debug("_unparsed has: {}".format(_unparsed))

    # find Catalogs
    while len(_unparsed) > 0:
        for url in _unparsed:
            # when files use an empty prefix for themselves (which is sensible in 
            # the context of the file), it leaves a mess in the namespace manager ..
            # so we'll replace empty prefixes with one based on the url:
            old_prefixes = set([n[0] for n in the_graph.namespaces()])
            # prepare a sensible prefix for the new file too:

            # is the url enough to find and parse the rdf?
            fmt = rdflib.util.guess_format(url)
            try:
                the_graph.parse(url, format=fmt)
            except (FileNotFoundError, urllib.error.HTTPError):
                url2 = url.rstrip('#') + '.ttl'
                logging.info("FAIL with url {0}, trying again with {1}".format(url,url2))
                the_graph.parse(url2, format='turtle')
            except:
                logging.error("FAIL with url " + url)
                raise
            
            #full_url = url
            #logging.debug("looking for {}".format(full_url))
            #fmt = rdflib.util.guess_format(full_url)
            #if fmt is None:
            #    # probably a local/direct .ttl file 
            #    full_url = url.rstrip('#') + '.ttl'
            #    fmt = rdflib.util.guess_format(full_url)
            #if fmt is None:
            #    raise Exception("I don't know how to parse {}".format(full_url))
            #
            #graph.parse(full_url, format=fmt)

            new_prefixes = set([n[0] for n in the_graph.namespaces()]) - old_prefixes
            if '' in new_prefixes:
                ns = [n[1] for n in the_graph.namespaces() if n[0]==''][0]
                rename = url[url.rfind('/')+1:].rstrip('#')
                logging.debug("replacing prefix for {0} with {1}".format(str(ns),rename))
                the_graph.namespace_manager.bind(rename, ns, replace=True, override=True)
            #logging.debug("_parsed {}".format(url))
            logging.debug("namespaces are now: {}".format(str([ns for ns in the_graph.namespaces()])))
            _parsed.add(str(url))
        logging.debug("_parsed has: {}".format(_parsed))
        _unparsed = set()   
        if spider:
            for remote in the_graph.query(q_remotes):
                url = str(remote['uri'])
                #logging.debug("found remote {}".format(remote))
                #logging.debug(url)
                if not url in _parsed:
                    _unparsed.add(url)
        # find LogSets (ie actual log metadata)
        for logset in the_graph.query(q_logsets):
            #logging.debug("found logset {}".format(logset))
            #logging.debug(url)
            url = str(logset['uri'])
            if not url in _parsed:
                _unparsed.add(url)
        logging.debug("_unparsed has: {}".format(_unparsed))
    return the_graph

from rdflib.namespace import Namespace
from typing import Dict
_namespaces: Dict[str,Namespace] = {}
def _find_namespaces() -> None:
    global _namespaces
    _namespaces = { n[0]: Namespace(n[1]) for n in the_graph.namespaces() }

def getns(prefix: str) -> Namespace:
    """ given a prefix, return the namespace (why isn't this part of rdflib?) """
    global _namespaces
    ns = _namespaces.get(prefix, None)
    if ns is None:
        # rescan the graph for namespaces:
        _find_namespaces()
        ns = _namespaces[prefix] # will raise KeyError if still can't find it
    return ns

from rdflib.term import URIRef
from typing import Union
def geturi(ident: Union[str,URIRef]) -> URIRef:
    if isinstance(ident, str):
        ns,sep,rdf_thing = ident.partition(':')
        ident = getns(ns)[rdf_thing]
    return ident

# hmm, not reliable because rdflib makes up new prefies
def get_shorthand(uri:Union[str,URIRef]) -> str:
    """ opposite of geturi - return it in prefix:name format """
    ns,sep,name = str(uri).rpartition('#')
    prefixes = {str(n[1]): n[0] for n in the_graph.namespaces() }
    logging.info("found prefixes: {0}".format(prefixes))
    return '{0}:{1}'.format(prefixes[ns+sep],name)
    

from typing import Generator
def prefixes() -> Generator[str,None,None]:
    """ yield prefixes currently used by the graph """
    if len(_namespaces) == 0:
        _find_namespaces()
    for prefix in _namespaces.keys():
        yield prefix

def query(*args, **kwargs):
    return the_graph.query(*args, **kwargs)

def subgraph(prefix: str) -> rdflib.ConjunctiveGraph:
    """ return a graph of just the triples where the subject is in this prefix """
    new = rdflib.ConjunctiveGraph()
    all_prefixes = set([p for p in prefixes()])
    added = all_prefixes - _predefined_prefixes.keys() - _preferred_prefixes.keys()
    ns = getns(prefix) 

    query = ''' SELECT ?s ?p ?o WHERE {{
                  ?s ?p ?o .
                  FILTER(STRSTARTS(STR(?s), "{0}")) .
                }}
            '''.format(str(ns))
    result = the_graph.query(query)
    for row in result:
        new.add(row)
    # we want the blank nodes that belong to nodes in this namespace too:
    # (there's probably a more elegant combined query for this, but I can't 
    # think of it so using 2 queries)
    query = ''' SELECT ?b ?p2 ?o WHERE {{
                  ?s ?p1 ?b .
                  ?b ?p2 ?o .
                  FILTER(isBlank(?b)) .
                  FILTER(STRSTARTS(STR(?s), "{0}")) .
                }}
            '''.format(str(ns))
    result = the_graph.query(query)
    for row in result:
        new.add(row)

    _bind_namespaces(new)
    new.namespace_manager.bind('', ns, replace=True, override=True)

    return new

import unittest
class TestLogsGraph(unittest.TestCase):

    def setUp(self):
        import os
        root = os.path.dirname(os.path.abspath(__file__))
        global base
        base = os.path.realpath('{0}/../../etc/'.format(root))+os.sep

    def test_construct(self):
        g = construct()
        self.assertEqual(len(g),137)

if __name__ == '__main__':
    unittest.main()






