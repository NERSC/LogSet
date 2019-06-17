#!/usr/bin/env python3
""" replacement namespace_manager

default NamespaceManager doesn't handle prefix/namespace binds correctly,
also, none of the store plugins seem to either. Does the store really need to
keep track of the prefixes? (what does it use them for?). Try redefining
the namespacemanager to handle binding locally-only.
"""

import sys
if sys.version_info < (3,6):
    raise Exception("Requires python 3.6+")

import logging as logger 
#logger = logging.getLogger(__name__)

import typing as t

import rdflib
import rdflib.namespace as ns

# namespace <-> prefix is a bidirectional 1:1 mapping
import bidict
import six

class PrefixInUse(Exception):
    """ Attempted to bind to an already-in-use prefix without replacing it """
    pass

class NamespaceAlreadyBound(Exception):
    """ Attempted to bind an already-bound namespace without overriding the binding """
    pass

class LocalNM(ns.NamespaceManager):
    """ NamespaceManager that doesn't trust or use the store for namespace management
        at all (ok, just a little: check the store for prefixes at initialization)
        (Note: should perhaps add a method to write prefixes back to the store, but 
        I think prefixes should be local to an application, not a store)
    """

    def __init__(self, graph=None):
        """ base NameSpaceManager needs graph argument, but uses it only to do the thing
            this class exists to prevent, so we set a default of None
        """
        self._namespaces: bidict.BidirectionalMapping[str,rdflib.URIRef] = bidict.bidict()
        super().__init__(graph)

    @property
    def store(self):
        """ the base NamespaceManager provides the graph's store as a property only to
            (as far as I can see) allow some external thing to reach through the
            NamespaceManager and the Graph and directly access the store. I think this
            breaks encapsulation and introduces tight coupling, and the only
            circumstance I can see it in use is in the sparql Prologue object, which
            makes a dummy/empty Graph() for itself to use in this way.
            At the cost of potentially breaking compatibility, I'm breaking the coupling
            by making store point to self instead, so that any attempt to reach through
            the namespacemanager will just get the namespacemanager
        """
        return self

    def namespaces(self) -> t.Generator[t.Tuple[str, rdflib.URIRef],None,None]:
        return ((prefix,namespace) for prefix,namespace in self._namespaces.items())

    def prefix(self, namespace: rdflib.URIRef, default=None) -> str:
        # for normalizeUri and compute_qname to use
        return self._namespaces.inverse.get(namespace, default)

    def namespace(self, prefix: str, default=None) -> rdflib.URIRef:
        # for compute_qname to use
        return self._namespaces.get(prefix, default)

    def term(self, qname) -> rdflib.URIRef:
        """ reverse of qname (why isn't there a utility for this already?) """
        prefix, sep, name = qname.partition(':')
        return ns.Namespace(self._namespaces[prefix]).term(name)

    def bind_from(self, graph):
        if not graph.store:
            return
        for prefix, namespace in graph.store.namespaces():
            self.bind(prefix, namespace)

    def bind(self, prefix, namespace, override=True, replace=False):
        ## see and fix /global/homes/s/sleak/Software/rdflib/rdflib/namespace.py
        #raise NotImplementedError

        prefix = prefix or '' # must be a string
        namespace = rdflib.URIRef(six.text_type(namespace))

        bound_namespace = self.namespace(prefix)
        bound_prefix = self.prefix(namespace)

        if bound_namespace is None and bound_prefix is None:
            # easy case: neither prefix nor namespace is set yet
            logger.debug(f"binding {prefix} to {namespace}")
            self._namespaces[prefix] = namespace
            return

        if bound_namespace==namespace and bound_prefix==prefix:
            # another easy case: nothing to do:
            logger.debug(f"not binding {prefix} to {namespace} - already bound")
            return

        if not replace and bound_namespace is not None:
            # in the base class, the prefix would be modified until an unused one is
            # found, and that would be bound to the namespace. Instead of quietly
            # binding something different to what was requested, raise an error:
            raise PrefixInUse(f"{prefix} is already bound to {bound_namespace}")

        if not override:
            if bound_prefix is not None and bound_prefix.startswith("_"):
                # in the base class, if the prefix startswith("_") then override is 
                # deemed true, with a comment about generated prefixes. I haven't found
                # any notes about generated prefixes elsewhere, and grepping for "_" is
                # a hopeless proposition, so I'll try to catch it in the wild and work 
                # out where this undocumented spec came from:
                raise Exception("Why is this here?")
            if bound_prefix:
                raise NamespaceAlreadyBound(f"{namespace} is already bound to {bound_prefix}")
        logger.debug(f"changing binding of {prefix} from {self._namespaces[prefix]} to {namespace}")
        self._namespaces[prefix] = namespace


