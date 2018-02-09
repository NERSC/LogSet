#!/usr/bin/env python3
""" read/write/manage the RDF/Turtle knowledge graph """

# system python 3 on Cori is broken so user will need to load a 
# python module, which will be 3.6+ anyway, so we'll take advantage
# of some of python's modern features:
import sys
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+")

import rdflib
import logging

graph: rdflib.ConjunctiveGraph = None
# the vocabulary and data dictionary are particularly important namespaces:
gddict: rdflib.ConjunctiveGraph = None
gvocab: rdflib.ConjunctiveGraph = None

def construct(*catalog_urls, local_only=True):
    """ starting with one or more catalog urls, parse the catalogs
        and optionally any peers, then build out the graph by fetching
        and reading all of the datasets
    """
    if len(catalog_urls)==0:
        raise Exception("must provide something to read!")

    global graph
    graph = rdflib.ConjunctiveGraph()
    for url in catalog_urls:
        fmt = rdflib.util.guess_format(url)
        graph.parse(url, format=fmt)

    # I suspect that for the query I need to read in the vocab,
    # so it knows what a logset:peers is?
            #vns = dict([n for n in gvocab.namespaces()])
    # ah, or define the prefix
    # reading the vocab is more elegant i think

    if not local_only:
        q_peers = '''PREFIX dcat: <http://www.w3.org/ns/dcat#>
                     PREFIX logset: <file:///global/u1/s/sleak/Monitoring/Resilience/LogSet/etc/vocab#>
                     SELECT ?uri
                   WHERE {
                      ?cat a dcat:Catalog .
                      ?cat logset:peers ?uri .
                   } '''
        #graph.bind()
        #q_peers = ''' SELECT ?uri
        #           WHERE {
        #              ?cat a dcat:Catalog .
        #              ?cat logset:peers ?uri .
        #           } '''
        for cat in query(q_peers):
            print(cat)
        


def read(*catalog_urls, vocab=None, ddict=None, local_only=True):
    """ build a graph starting from the provided urls and finding the 
        vocabulary, dictionary and peer catalogs on the web. If 
        local_only, don't spider for other catalogs
    """
    if len(catalog_urls)==0:
        raise Exception("must provide something to read!")

    global graph, gddict, gvocab
    if vocab is not None:
        if gvocab is not None:
            # FIXME check that vocabs are same:
            vns = dict([n for n in gvocab.namespaces()])
        fmt = rdflib.util.guess_format(vocab)
        gvocab = rdflib.ConjunctiveGraph().parse(vocab, format=fmt)
    if gvocab is None:
        raise Exception("need a vocabulary!")
    print(gvocab.serialize(format='n3').decode('ascii'))

    if ddict is not None:
        if gddict is not None:
            # FIXME check that ddicts are same:
            dns = dict([n for n in gddict.namespaces()])
        fmt = rdflib.util.guess_format(ddict)
        gddict = rdflib.ConjunctiveGraph().parse(ddict, format=fmt)
    print(gddict.serialize(format='n3').decode('ascii'))

    if graph is None:
        #graph = rdflib.ConjunctiveGraph()
        graph = gvocab + gddict
    for url in urls:
        fmt = rdflib.util.guess_format(url)
        graph.parse(url, format=fmt)
    #print(graph.serialize(format='n3').decode('ascii'))

    # now find the catalogs:


def _spider():
    # look for catalogs, fetch/read them and incorporate their 
    # datasets into the graph:
    q_peers = '''SELECT ?uri
               WHERE {
                  ?cat a dcat:Catalog .
                  ?cat logset:peers ?uri .
               } '''
    #for cat in query(q_peers):
        


    # find datassts in catalogs
    # (actaully could probably just query for things of type dataset)
    #q_datasets = '''SELECT ?uri 
    #           WHERE {
    #              ?cat a dcat:Catalog .
    #              ?cat dcat:dataset ?uri .
    #           } '''
    #for cat in query(cat_query):
    #    print(cat)

def query(query):
    return graph.query(query)

def dump():
    print(graph.serialize(format='n3').decode('ascii'))

