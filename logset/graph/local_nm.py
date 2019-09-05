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

    # hmm, bidict is handy but has a limitation: what if different graphs in the 
    # same conjunctivegraph use different prefixes to refer to the same namespace?
    # keep a list of secondary prefixes (namespace can be repeated)
    

    def __init__(self, graph=None):
        """ base NameSpaceManager needs graph argument, but uses it only to do the thing
            this class exists to prevent, so we set a default of None
        """
        self._canonical: bidict.BidirectionalMapping[str,rdflib.URIRef] = bidict.bidict()
        self._secondary: t.Dict[str,rdflib.URIRef] = dict()
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
        return ((prefix,namespace) for prefix,namespace in self._canonical.items())

    def prefix(self, namespace: rdflib.URIRef, default=None) -> str:
        # for normalizeUri and compute_qname to use
        return self._canonical.inverse.get(namespace, default)

    def namespace(self, prefix: str, default=None) -> rdflib.URIRef:
        # for compute_qname to use
        return self._canonical.get(prefix, self._secondary.get(prefix, default))

    def term(self, qname) -> rdflib.URIRef:
        """ reverse of qname (why isn't there a utility for this already?) """
        prefix, sep, name = qname.partition(':')
        if prefix in self._canonical or prefix in self._secondary:
            return ns.Namespace(self.namespace(prefix)).term(name)
        else:
            raise KeyError(prefix)
        #return ns.Namespace(self._canonical[prefix]).term(name)

    def bind_from(self, graph):
        if not graph.store:
            return
        for prefix, namespace in graph.store.namespaces():
            self.bind(prefix, namespace)

    def bind(self, prefix, namespace, override=True, replace=False):
        ## see and fix /global/homes/s/sleak/Software/rdflib/rdflib/namespace.py
        #raise NotImplementedError
        # from the original source, the intention is:
        #    bind a given namespace to the prefix
        #    if override, rebind, even if the given namespace is already bound to another prefix.
        #    if replace, replace any existing prefix with the new namespace

        prefix = prefix or '' # must be a string
        namespace = rdflib.URIRef(six.text_type(namespace))

        # a blank prefix is always secondary and can be overwritten with impunity:
        if not prefix:
            self._secondary[prefix] = namespace
            return

        bound_namespace = self.namespace(prefix)
        bound_prefix = self.prefix(namespace)

        if bound_namespace is None and bound_prefix is None:
            # easy case: neither prefix nor namespace is set yet
            logger.debug(f"binding {prefix} to {namespace} (1)")
            self._canonical[prefix] = namespace
            return

        if bound_namespace==namespace and bound_prefix==prefix:
            # another easy case: nothing to do:
            logger.debug(f"not binding {prefix} to {namespace} - already bound")
            return

        if bound_namespace==namespace and self._secondary.get(prefix)==namespace:
            if bound_prefix is None:
                # secondary binding like this exists, and namespace is not primarily
                # bound to a different prefix, so we can promote the secondary binding:
                logger.debug(f"promoting {prefix} -> {namespace} from secondary")
                del self._secondary[prefix]
                self._canonical[prefix] = namespace
            else:
                # can't safely promote, but secondary binding already exists:
                logger.debug(f"not binding {prefix} to {namespace} - already (secondarily) bound")
            return

        if bound_namespace is not None:
            if not replace:
                # in the base class, the prefix would be modified until an unused one is
                # found, and that would be bound to the namespace. Instead of quietly
                # binding something different to what was requested, raise an error:
                # HOWEVER: if prefix is '', deem replace to be true
                logger.debug(f"attempting to bind {prefix} to {namespace}")
                raise PrefixInUse(f"{prefix} is already bound to {bound_namespace}")
            else: 
                logger.debug(f"binding {prefix} to {namespace} (2)")
                self._canonical[prefix] = namespace

        if bound_prefix is not None:
            # this namespace is already associated with a prefix. In the base class,
            # if the prefix startswith("_") then override is deemed true, with a
            # comment about generated prefixes. I haven't found any notes about generated
            # prefixes elsewhere, but generating a dummy prefix when the prefix is 
            # blank (eg for "this ttl file") is a plausible use-case, and those generated
            # prefixes should always be secondary to a user-specified prefix: 
            if override or bound_prefix.startswith('_'):
                logger.debug(f"demoting {bound_prefix} and binding {prefix} to {namespace}")
                self._secondary[bound_prefix] = self._canonical.pop(bound_prefix)
                self._canonical[prefix] = namespace
            elif prefix not in self._secondary: 
                # if not override, its still useful for the prefix to point to the 
                # namespace, but don't replace an existing secondary prefix
                logger.debug(f"secondary binding {prefix} to {namespace} to leave {bound_prefix} in place")
                self._secondary[prefix] = namespace
            else:
                raise NamespaceAlreadyBound(f"{namespace} is already bound to {bound_prefix}")


