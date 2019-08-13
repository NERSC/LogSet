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

# namespace management: prefixes we prefer to associate with key namespaces:
base: str = config.settings["namespaces"]["base"]
# FIXME this should probably be in config too
preferred_prefixes: t.Dict[str,str] = {
    str(rdflib.namespace.RDF):          'rdf',
    str(rdflib.namespace.RDFS):         'rdfs',
    str(rdflib.namespace.OWL):          'owl',
    str(rdflib.namespace.XSD):          'xsd',
    str(rdflib.namespace.FOAF):         'foaf',
    str(rdflib.namespace.SKOS):         'skos',
    str(rdflib.namespace.DOAP):         'doap',
    str(rdflib.namespace.DC):           'dc',
    str(rdflib.namespace.DCTERMS):      'dct',
    str(rdflib.namespace.XMLNS):        'xml',
    'http://www.w3.org/ns/dcat#':       'dcat',
    'https://www.w3.org/2006/vcard/ns': 'vcard',
    'http://www.w3.org/ns/adms#':       'adms',
    f'{base}/logset#':                  'logset',
    f'{base}/ddict#':                   'ddict',
}

import rdflib.namespace as ns
well_known_namespaces = { 
    prefix: ns.Namespace(url) for url,prefix in preferred_prefixes.items()
}

# well-known namespaces that we use in uris, but don't use semantically, so
# no need to include them in the graph (especially, dcterms appears to be down
# at the moment which breaks constructing the graph if we need to parse it)
external_namespaces: t.Set[str] = set(
    ns for ns,prefix in preferred_prefixes.items() if prefix in
    ('rdf', 'rdfs', 'owl', 'xsd', 'skos', 'doap', 'dc', 'dct',
     'dcat', 'vcard', 'xml', 'logset', 'ddict')
)

# actually:
#   with LogSetGraph(persistence, path, create, clobber) as g:
#     g.extend(..) etc
# .. and persistence can be a local ttl file too


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
        for p, ns in well_known_namespaces.items():
            self.namespace_manager.bind(p, ns, override=True, replace=True)

        for attr, value in kwargs.items():
            if not hasattr(self, attr):
                setattr(self, attr, value)

    def __enter__(self):
        if len(self)==0:
            self.construct()
        # on first open/entry, should probably sanity check that the graph?
        # (or maybe, assume all is well and upon querying for info, then report
        # "this graph has unknown parts")
        logger.info(f"on entry, graph has {len(self)} triples")
        logger.debug(f"and these namespaces: {list(self.namespace_manager.namespaces())}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.commit()

    def construct(self):
        if len(self)!=0:
            return
        logger.info("constructing the basic graph")
        for url, prefix in preferred_prefixes.items():
            self.namespace_manager.bind(prefix, url, override=True, replace=True)
        self.extend(f"{config.etc}/logset#", f"{config.etc}/ddict#")
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
        done: t.Set[str] = set(str(n[1]) for n in self.namespaces()) | external_namespaces
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

    def ingest(self, url: str) -> None:
        """ incorporate the triples at url into this graph as a new context """
        if not (url.startswith('http:') or url.startswith('https:')):
            url = 'file://' + os.path.abspath(url.replace('file://', '', 1))

        uri = rdflib.URIRef(url)

        # do we already have this uri?
        uri_in_graph = """ SELECT ?uri WHERE {
                       ?thing a adms:AssetDistribution .
                       ?thing dcat:downloadURL ?uri .
                     }
                 """
        if uri in self.default_context.query(uri_in_graph, initNs=well_known_namespaces):
            raise GraphExistsError(f"graph already has {uri}")

        #nm = local_nm.LocalNM()
        # read into an in-memory graph because the backends do a commit-per-triple
        # which makes parsing the url painfully slow:
        g = rdflib.Graph(identifier=uri, namespace_manager=self.namespace_manager)
        fmt = rdflib.util.guess_format(uri)
        try:
            logger.info(f"\ntrying to parse {uri} with format {fmt}")
            g.parse(uri, format=fmt)
        except (FileNotFoundError, urllib.error.HTTPError):
            uri = rdflib.URIRef(f"{url.rstrip('#')}.ttl")

            # check again for if this uri is already here too
            if uri in self.default_context.query(uri_in_graph, initNs=well_known_namespaces):
                raise GraphExistsError(f"graph already has {uri}")

            logger.info(f"trying again with {uri}")
            g.parse(uri, format='turtle')
        except rdflib.plugins.parsers.notation3.BadSyntax as e:
            logger.critical(f"Syntax error in {uri}: {e}")
            sys.exit(1)
        except:
            raise

        # describe the thing I just passed:
        thing = uri
        # FIXME: find what it refers to itself as (eg what if anything does it 
        # include as myprefix:) and use that for thing
        nm = self.namespace_manager
        g.add((thing, nm.term('rdf:type'), nm.term('adms:AssetDistribution')))
        g.add((thing, nm.term('dcat:downloadURL') ,uri))

        # TODO pull out the triples with blank nodes, because we will need to replace the 
        # blank nodes with blank nodes from self, to avoid collisions

        # TODO bind/merge the namespaces
        my_namespace = ''
        for prefix, namespace in g.namespaces():
            logger.debug(f"preparing to bind {prefix} -> {namespace}")
            if prefix == '':
                # blank prefix usually indicates the namespace associated with the url we 
                # are ingesting, so remember it:
                logger.debug(f"skipping empty prefix, remembering {namespace}")
                my_namespace = namespace
                continue
            try:
                # namespace bindings in existing graph get priority
                # ah: but if the existing binding has a prefix like _blah, then it was 
                # autogenerated, and an explicitly chosen one is better
                self.namespace_manager.bind(prefix, namespace, override=False, replace=False)
                logger.info(f"bound {prefix}: {namespace}")
            except local_nm.PrefixInUse:
                #if prefix:
                # what's best to do here? perhaps inform the user and let them rebind later
                logger.warning(f"dropping binding of '{prefix}' -> {namespace}")
            except local_nm.NamespaceAlreadyBound:
                logger.info(f"skipping already bound {prefix} -> {namespace}")
                pass

        if my_namespace:
            if not self.namespace_manager.prefix(my_namespace):
                # make a dummy prefix starting with "_" (to indicate it was generated)
                # and looking a bit like the url basename (to hint where it came from)
                hint = re.match('\w+', uri.rpartition('/')[2].lower()).group(0)
                prefix = ''.join(['_',hint,'_',ran_str(4)])
                logger.info(f"attempting to rebind {prefix} to {my_namespace}")
                try:
                    self.namespace_manager.bind(prefix, my_namespace, override=False, replace=False)
                except local_nm.NamespaceAlreadyBound:
                    pass # its ok to not bind a dummy prefix
            else:
                logger.info(f"found my namespace {my_namespace} bound to {self.namespace_manager.prefix(my_namespace)}")

        # now make sure the store is updated:
        # note that namespace management in sqlalchemy store (at least) is incomplete,
        # it simply tries to insert a new namespace record, failing due to UniqueConstraint
        # it is it already there. And there is no provision for unbinding a prefix. So, 
        # work around it:
        for prefix, namespace in self.namespaces():
            # find out what the store knows:
            p = self.store.prefix(namespace)
            n = self.store.namespace(prefix)
            if prefix and not n and not prefix.startswith('_'):
                # why doesn't this stay recorded in the store?
                logger.info(f"binding {prefix} -> {namespace} in store")
                self.store.bind(prefix, namespace)
            else:
                logger.info(f"not binding {prefix} -> {namespace} in store because n is {n} or {prefix} has _")

        new_context = self.get_context(uri)
        quads = ((s,p,o,new_context) for s,p,o in g.triples((None,None,None)))
        new_context.addN(quads)

#    def _try_to_parse(self, url:str) -> None:
#        fmt = rdflib.util.guess_format(url)
#        try:
#            logger.info(f"trying to parse {url} with format {fmt}")
#            self.parse(url, format=fmt)
#        except (FileNotFoundError, urllib.error.HTTPError):
#            logger.info(f"trying again with as {url.rstrip('#')}.ttl")
#            self.parse(f"{url.rstrip('#')}.ttl", format='turtle')
#        except rdflib.plugins.parsers.notation3.BadSyntax as e:
#            logger.critical(f"Syntax error in {url}: {e}")
#            sys.exit(1)
#        except:
#            raise
#
#    # FIXME with localnm this might not be needed
#    def _canonicalize_namespaces(self) -> None:
#        """ ensure the prefix we have for each namespace is predictable """
#        readable = lambda seq: '\n'.join(str(i) for i in seq)
#        logger.info(f"canonicalizing from {readable(self.namespaces())}")
#        rebinds: t.Dict[rdflib.term.URIRef,str] = {}
#        for prefix,ns in self.namespaces():
#            url = str(ns)
#            if prefix == '':
#                # turtle files typically use an empty prefix for "this file",
#                # replace it with one based on the url:
#                prefix = url[url.rfind('/')+1:].rstrip('#')
#                rebinds[ns] = prefix
#                logger.info(f"found empty prefix for {url}, rebinding to {prefix}")
#                # rdflib currently doesn't correctly remove empty prefixes, which 
#                # leads to a subsequent parsing with an empty prefix to rebind this 
#                # namespace to an arbitrary prefix. Carefully prevent this:
#                # (FIXME with a future version of rdflib, this should not be required)
#                rebinds[''] = None
#            # note fall through to checking for preferred prefixes
#            if url in preferred_prefixes:
#                preferred = preferred_prefixes[url]
#                if prefix != preferred:
#                    rebinds[ns] = preferred
#                    logger.info(f"found better prefix {preferred} for {url}, rebinding from {prefix}")
#        for ns, prefix in rebinds.items():
#            logger.info(f"doing rebinding {prefix} to {ns}")
#            #self.namespace_manager.bind(prefix, ns, replace=True)
#            self.namespace_manager.bind(prefix, ns, override=True, replace=True)
#            #self.bind(prefix, rdflib.namespace.Namespace(ns), override=True, replace=True)
#            logger.info(f"namespaces are now {readable(self.namespaces())}")

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

