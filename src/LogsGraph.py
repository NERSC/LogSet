#!/usr/bin/env python3
""" read/write/manage the RDF/Turtle knowledge graph """

import logging
import sys
logging.debug(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

import rdflib

graph: rdflib.ConjunctiveGraph = None

# when constructing or extending a graph the new rdf/ttl file might invoke 
# still more new namespaces, so we take an iterative 2-phase approach of 
# collecting urls to prase, and parsing them:
_parsed = set()
_unparsed = set()

import os
def construct(*catalog_urls: str, spider=False) -> rdflib.ConjunctiveGraph:
    """ starting with one or more catalog urls, parse the catalogs
        and optionally any peers, then build out the graph by fetching
        and reading all of the datasets.
        Note that this will clear and replace an existing graph.
    """
    global graph, _parsed, _unparsed
    graph = rdflib.ConjunctiveGraph()
    # the logset vocab definition and data dictionaries have a common,
    # well-known source of truth, parse them just once, the first time:
    # base = 'https://raw.githubusercontent.com/NERSC/LogSet/master/etc/',
    base = 'http://portal.nersc.gov/project/mpccc/sleak/resilience/datasets/'
    _unparsed = set([base+'logset#', base+'dict#'])

    _parsed = set()
    logging.debug("_parsed has: {}".format(_parsed))
    
    extend(*catalog_urls, spider=spider)
    # bind well-known namespaces to well-known prefixes:
    graph.bind('logset', base+'logset#')
    graph.bind('dcat', 'http://www.w3.org/ns/dcat#')
    #graph.bind('dict', base+'dict#')
    #graph.bind('adms', 'http://www.w3.org/ns/adms#')

    # note rdflib provides these, bind for common lowercase usage:
    graph.bind('rdf', rdflib.namespace.RDF)
    graph.bind('rdfs', rdflib.namespace.RDFS)
    graph.bind('owl', rdflib.namespace.OWL)
    graph.bind('xsd', rdflib.namespace.XSD)
    graph.bind('foaf', rdflib.namespace.FOAF)
    graph.bind('skos', rdflib.namespace.SKOS)
    graph.bind('doap', rdflib.namespace.DOAP)
    graph.bind('dc', rdflib.namespace.DC)
    graph.bind('dct', rdflib.namespace.DCTERMS)
    return graph


def extend(*new_urls: str, spider=False) -> rdflib.ConjunctiveGraph:
    """ extend the graph with the currently-unparsed urls """
    global graph, _parsed, _unparsed
    q_remotes = ''' SELECT ?uri WHERE
                    { ?cat a dcat:Catalog .
                       ?cat rdfs:seeAlso ?uri . } '''
    q_logsets = '''SELECT ?uri WHERE 
                     { ?cat a dcat:Catalog .
                       ?cat dcat:dataset ?uri . }'''

    for url in new_urls:
        if url not in _parsed:
            _unparsed.add(url)
    logging.debug("_unparsed has: {}".format(_unparsed))

    # find Catalogs
    while len(_unparsed) > 0:
        for url in _unparsed:
            # TODO for now, we assume the file is .ttl and parse accordingly
            # eventually we might use urllib to check for possible file 
            # extentions and guess format with rdflib.util.guess_format(url)
            if url.endswith('#'):
                full_url = str(url)[:-1] + '.ttl' 
            else:
                full_url = url
            logging.debug("looking for {}".format(full_url))
            fmt = rdflib.util.guess_format(full_url)
            graph.parse(full_url, format=fmt)
            #logging.debug("_parsed {}".format(url))
            logging.debug("namespaces are now: {}".format(str([ns for ns in graph.namespaces()])))
            _parsed.add(str(url))
        logging.debug("_parsed has: {}".format(_parsed))
        _unparsed = set()   
        if spider:
            for remote in graph.query(q_remotes):
                url = str(remote['uri'])
                #logging.debug("found remote {}".format(remote))
                #logging.debug(url)
                if not url in _parsed:
                    _unparsed.add(url)
        # find LogSets (ie actual log metadata)
        for logset in graph.query(q_logsets):
            #logging.debug("found logset {}".format(logset))
            #logging.debug(url)
            url = str(logset['uri'])
            if not url in _parsed:
                _unparsed.add(url)
        logging.debug("_unparsed has: {}".format(_unparsed))
    return graph


def getns(prefix):
    """ given a prefix, return the namespace (why isn't this part of rdflib?) """
    return [rdflib.Namespace(n[1]) for n in graph.namespaces() if n[0]==prefix][0]

# may not work anymore (updated getns to return actual namespace)
#def get(prefix, item):
#    """ retreive a well-known node by name, eg logset:ConcreteLog """
#    return rdflib.URIRef(getns(prefix) + item)
#    # this is only valid for triples:
#    #if (concretelog,rdflib.RDF.type,rdflib.OWL.Class) not in graph:
#    #    raise Exception("someting is wrong")








