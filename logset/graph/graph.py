#!/usr/bin/env python3
""" logset-specific wrapper for RDFlib ConjunctiveGraph """

# Naming conventions:
#  path: str - a file path on a local filesystem
#  url: str  - a protocol + path for an actual location, eg 
#                file://blah.txt of file:///home/me/blah.txt or http://my.org/file
#              If the protocol is missing, assume 'file://'
#  uri: rdflib.URIRef - an identifier (not a string, and not necessarily an actual location)
#  qname: str - prefix:name 


import sys
if sys.version_info < (3,6):
    raise Exception("Requires python 3.6+")

from .. import config

# I hate python logging
import logging as logger
#logger = logging.getLogger(__name__)

import typing as t

# registry and factory method to instantiate LogSetGraphs (subclasses of 
# LogSetGraphBase for a specific storage method should override __init__,
# __enter__ and __exit__ as appropriate, and map the persistence types they
# support to themself)
graph_classes: t.Dict[str,t.Type['LogSetGraphBase']] = {}

def LogSetGraph(persistence: str='', # type of local persistence (store) to use
                path: str='',        # local place to persist to ('' is default)
                create: bool=True,   # create local persistence if necessary?
                clobber: bool=False  # overwrite/replace whatever is at path?
    ) -> 'LogSetGraphBase':
    persistence=persistence or config.settings['persistence']['persistence']
    path=path or config.settings['persistence']['name']
    T = graph_classes[persistence]
    logger.info(f"instantiating a {T.__name__} with {persistence}, {path}, {create}, {clobber}")
    return T(persistence=persistence, path=path, create=create, clobber=clobber)

import rdflib
import urllib.error

import rdflib.plugins.sparql as sparql
import tempfile
from . import local_nm

# used to generate an obviously-dummy prefix for a namespace when we don't have one
import random, string
def ran_str(len):
    """ return a string of random letters, of a given length """
    return ''.join([random.choice(string.ascii_lowercase) for i in range(len)])

import re

class GraphExistsError(Exception):
    """ Attempted to parse a url that is already in the local graph """
    pass

import rdflib.plugins.parsers.notation3 as notation3

import rdflib.namespace as ns
_csn=config.settings['namespaces'] # shorthand
well_known_namespaces = { 
    prefix: ns.Namespace(_csn[prefix]) for prefix in _csn
}
_csb=config.settings['bindings'] # shorthand
well_known_namespaces.update({
    prefix: ns.Namespace(_csb[prefix]) for prefix in _csb
})

class LogSetGraphBase(rdflib.ConjunctiveGraph):
    """ a graph based on the LogSet vocabulary """

    # rdflib.ConjunctiveGraph.__init__ doesn't take a NM argument (why not?)
    def __init__(self, **kwargs):
        """ kwargs can include rdflib ConjunctiveGraph args:
                store,
                identifier,
            And LogSetGraph args:
                persistence: str='', # type of local persistence (store) to use
                path: str='logs.db', # local place to persist to
                create: bool=True,   # create local persistence if necessary?
                clobber: bool=False  # overwrite/replace whatever is at path?
            kwargs become attributes.
        """
        a = {arg:val for arg,val in kwargs.items() if arg in ('store', 'identifier')}
        super().__init__(**a)

        # rdflib.ConjunctiveGraph.__init__ doesn't take a NM argument but instead
        # uses the Graph default, which is to instantiate a NamespaceManager lazily.
        # But NamespaceManager is flaky, so we'll use a local one:
        self.namespace_manager = local_nm.LocalNM()
        for prefix,namespace in well_known_namespaces.items():
            self.namespace_manager.bind(prefix, namespace, override=False, replace=False)

        for attr, value in kwargs.items():
            if not hasattr(self, attr):
                setattr(self, attr, value)

    def __enter__(self):
        self.construct()
        # on first open/entry, should probably sanity check the graph?
        # (or maybe, assume all is well and upon querying for info, then report
        # "this graph has unknown parts")
        logger.info(f"on entry, graph has {len(self)} triples")
        logger.debug(f"and these namespaces: {list(self.namespace_manager.namespaces())}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.commit()

    def construct(self):
        """ idempotent method that ensures base graph is ready to use """
        if len(self)!=0:
            return
        logger.info("constructing the basic graph")
        urls = [ config.settings['namespaces'][p] for p in config.settings['namespaces'] ]
        self.extend(*urls)
        self.extend(f"{config.etc}/logset#", f"{config.etc}/ddict#")
        for prefix, namespace in self.namespaces():
            logger.info(f"binding {prefix} -> {namespace} in store")
            self.store.bind(prefix, namespace)
        logger.info(f"after construction, graph has {len(self)} triples")
        logger.debug(f"and these namespaces: {list(self.namespace_manager.namespaces())}")


    # other known catalogs:
    _spiderquery = sparql.prepareQuery( """
        SELECT ?uri WHERE {
            ?cat a dcat:Catalog .
            ?cat rdfs:seeAlso ?uri .
        } """, initNs=well_known_namespaces )

    # logsets in catalogs:
    _logsetsquery = sparql.prepareQuery( """
        SELECT ?uri WHERE {
            ?cat a dcat:Catalog .
            ?cat dcat:dataset ?uri .
        } """, initNs=well_known_namespaces )

    def extend(self, *urls: str, spider: bool=False) -> None:
        """ add the tripes at these urls to the graph, and triples from any
            namespaces used by these urls (that are not already accounted for).
            Optionally also "spider" out to other catalogs referenced via
            rdfs:seeAlso properties in dcat:Catalog objects described in these
            urls
        """
        # need to add some more smarts: it needs to parse each url into a
        # named context, and it needs to add Asset descriptions for each url to 
        # the default context. It also needs to first check the contents of what it
        # parsed to see eg what the thing describes itself as, what it considers
        # to be its uri/namespace, and to add an assetdestribution to the default
        # context to record where it got this one from
        todo: t.Set[str] = set(url for url in urls)
        done: t.Set[str] = set(str(n[1]) for n in self.namespaces())
        while todo:
            # first we parse the urls we know we need:
            for url in todo:
                self.ingest(url)
                done.add(url)
            todo.clear()

            # next we add new urls from what we've parsed already to the todo list:
            if spider:
                new_urls = (str(t['uri']) for t in self.query(self._spiderquery))
                todo.update(u for u in new_urls if u not in done)

            new_urls = (str(t['uri']) for t in self.query(self._logsetsquery))
            todo.update(u for u in new_urls if u not in done)

            # other namespaces files used in the ones we just parsed
            # (but not the dummy '' prefix!)
            new_urls = (str(ns) for prefix,ns in self.namespaces() if prefix)
            todo.update(u for u in new_urls if u not in done)
        logger.info(f"after expand, graph has {len(self)} triples")

    def _collect(self, url: str) -> rdflib.Graph:
        """ attempt to read url into an in-memory subgraph, which can then be 
            added to the conjunctive graph
        """
        uri = rdflib.URIRef(url)
        if uri in self.contexts():
            raise GraphExistsError(f"graph already has {uri}")

        # read into an in-memory graph because the backends do a commit-per-triple
        # which makes parsing the url painfully slow. Each has it's own private 
        # namespace_manager to prevent clashes caused by ingesting from multiple 
        # sources
        nm = local_nm.LocalNM()
        g = rdflib.Graph(identifier=uri, namespace_manager=nm)
        fmt = rdflib.util.guess_format(uri)
        logger.info(f"\ntrying to parse {uri} with format {fmt}")
        try:
            g.parse(uri, format=fmt)
        except notation3.BadSyntax as e:
            logger.critical(f"Syntax error in {uri}: {e}")
            sys.exit(1)
        except:
            raise

        return g


    def ingest(self, url: str) -> None:
        """ incorporate the triples at url into this graph as a new context """
        if not (url.startswith('http:') or url.startswith('https:')):
            url = 'file://' + os.path.abspath(url.replace('file://', '', 1))

        try:
            g = self._collect(url)
        except GraphExistsError:
            pass
        except (FileNotFoundError, urllib.error.HTTPError):
            url = f"{url.rstrip('#')}.ttl"
            logger.info(f"trying again with {url}")
            g = self._collect(url)

        # TODO pull out the triples with blank nodes, because we will need to replace the 
        # blank nodes with blank nodes from self, to avoid collisions

        # we don't care about the namespace bindings from within the subgraph
        # TODO but we should label the subgraphs we explicitly added 
        # (maybe as part of the 'use' command)
        # (and info command should show contexts too)

        new_context = self.get_context(g.identifier)
        quads = ((s,p,o,new_context) for s,p,o in g.triples((None,None,None)))
        new_context.addN(quads)

graph_classes['None'] = LogSetGraphBase

import os
import shutil
def remove(path: str):
    """ merciless removal of whatever is at path """
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

_default_dbname = config.settings["persistence"]["name"]

class LogSetGraphInSleepycat(LogSetGraphBase):

    def __init__(self, **kwargs):
        self.path = kwargs.get('path', f"{_default_dbname}.db")
        super().__init__(store='Sleepycat', **kwargs)
        if self.clobber:
            remove(self.path)
        errcode = self.open(self.path, create=self.create)
        if errcode != rdflib.store.VALID_STORE:
            raise ConnectionError(f"could not open db at {self.path}, got {errcode}")

graph_classes['Sleepycat'] = LogSetGraphInSleepycat


import rdflib_sqlalchemy
rdflib_sqlalchemy.registerplugins()
class LogSetGraphInSQL(LogSetGraphBase):

    def __init__(self, **kwargs):
        store = rdflib.plugin.get("SQLAlchemy", rdflib.store.Store)()
        self.path = kwargs.get('path', f"{_default_dbname}.db")
        super().__init__(store=store, **kwargs)
        if self.clobber:
            remove(self.path)
        if self.persistence.lower().startswith('sqlite'):
            url = f"sqlite:///{self.path}"
            logger.info(f"creating sqlite db with {url}")
        else:
            raise NotImplementedError("can't handle {self.persistence} yet")
        errcode = self.open(url, create=self.create)
        if errcode != rdflib.store.VALID_STORE:
            raise ConnectionError(f"could not open db at {self.path}, got {errcode}")

graph_classes['SQLite3'] = LogSetGraphInSQL


class LogSetGraphInTurtleFile(LogSetGraphBase):

    def __init__(self, **kwargs):
        self.path = kwargs.get('path', f"{_default_dbname}.ttl")
        super().__init__(**kwargs)
        if self.clobber:
            remove(self.path)
        if not os.path.exists(self.path):
            logger.info(f"{self.path} does not exist yet, contruct it if {self.create} is True")
            if self.create:
                self._construct()
            else:
                raise FileNotFoundError(self.path)
        else:
            logger.info(f"reading the file at {self.path}")
            self.extend(self.path)
        with open(self.path, 'w') as f:
            f.write(self.serialize(format='turtle').decode('ascii'))

    def __exit__(self, exc_type, exc_value, traceback):
        # FIXME when is it safe/ok to overwrite the file?
        with open(self.path, 'w') as f:
            f.write(self.serialize(format='turtle').decode('ascii'))

graph_classes['Turtle'] = LogSetGraphInTurtleFile

