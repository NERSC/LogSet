#!/usr/bin/env python3
""" read/write/manage the RDF/Turtle knowledge graph """

# system python 3 on Cori is broken so user will need to load a 
# python module, which will be 3.6+ anyway, so we'll take advantage
# of some of python's modern features:
import sys
print(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+")

import rdflib
import logging

graph: rdflib.ConjunctiveGraph = None

# when constructing or extending a graph the new rdf/ttl file might invoke 
# still more new namespaces, so we take an iterative 2-phase approach of 
# collecting urls to prase, and parsing them:
parsed = set()
unparsed = set()

import os
def construct(*catalog_urls, spider=False):
    """ starting with one or more catalog urls, parse the catalogs
        and optionally any peers, then build out the graph by fetching
        and reading all of the datasets.
        Note that this will clear and replace an existing graph.
    """
    #if len(catalog_urls)==0:
    #    raise Exception("must provide something to read!")

    global graph, parsed, unparsed
    graph = rdflib.ConjunctiveGraph()
    # the logset vocab definition and data dictionaries have a common,
    # well-known source of truth, parse them just once, the first time:
    # base = 'https://raw.githubusercontent.com/NERSC/LogSet/master/etc/',
    base = 'http://portal.nersc.gov/project/mpccc/sleak/resilience/datasets/'
    unparsed = set([base+'logset#', base+'dict#'])

    parsed = set()
    logging.debug("parsed has: {}".format(parsed))
    
    extend(*catalog_urls, spider=spider)
    # bind well-known namespaces:
    graph.bind('logset', base+'logset#')
    graph.bind('dict', base+'dict#')
    return graph
    


def extend(*new_urls, spider=False):
    """ extend the graph with the currently-unparsed urls """
    global graph, parsed, unparsed
    q_remotes = ''' SELECT ?uri WHERE
                    { ?cat a dcat:Catalog .
                       ?cat rdfs:seeAlso ?uri . } '''
    q_logsets = '''SELECT ?uri WHERE 
                     { ?cat a dcat:Catalog .
                       ?cat dcat:dataset ?uri . }'''

    for url in new_urls:
        if url not in parsed:
            unparsed.add(url)
    logging.debug("unparsed has: {}".format(unparsed))

    # find Catalogs
    while len(unparsed) > 0:
        for url in unparsed:
            # for now, assume the file is .ttl and parse accordingly
            # eventually we might use urllib to check for possible file 
            # extentions and guess format with rdflib.util.guess_format(url)
            if url.endswith('#'):
                full_url = str(url)[:-1] + '.ttl' 
            else:
                full_url = url
            logging.debug("looking for {}".format(full_url))
            fmt = rdflib.util.guess_format(full_url)
            graph.parse(full_url, format=fmt)
            #logging.debug("parsed {}".format(url))
            logging.debug("namespaces are now: {}".format(str([ns for ns in graph.namespaces()])))
            parsed.add(str(url))
        logging.debug("parsed has: {}".format(parsed))
        unparsed = set()   
        if spider:
            for remote in graph.query(q_remotes):
                url = str(remote['uri'])
                #logging.debug("found remote {}".format(remote))
                #logging.debug(url)
                if not url in parsed:
                    unparsed.add(url)
        # find LogSets (ie actual log metadata)
        for logset in graph.query(q_logsets):
            #logging.debug("found logset {}".format(logset))
            #logging.debug(url)
            url = str(logset['uri'])
            if not url in parsed:
                unparsed.add(url)
        logging.debug("unparsed has: {}".format(unparsed))
    return graph









