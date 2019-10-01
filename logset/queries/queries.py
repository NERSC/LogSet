#!/usr/bin/env python3
""" sample/handy queries on a logset graph """

# note that all labels will have _ not -
#q = """
#SELECT ?node WHERE {
#  ?slot logset:hasPart ?node .
#  ?slot logset:hasPart ?aries .
#  ?aries logset:hasPart ?tile .
#  ?tile a craydict:Ptile .
#  ?tile rdfs:label "c5_1c1s8a0l54" .
#}
#"""

import logging as logger
#logger = logging.getLogger(__name__)

from .. import graph
import rdflib.namespace as ns

import typing as t
Qname = str # a string like prefix:name

class MultipleMatches(Exception):
    def __init__(self, query_fn: str, nmatches: int, on: str="", matches: str=""):
        onstr = f"{' on ' if on else ''}{on}"
        matchstr = f"{': ' if matches else ''}{matches}"
        self.message = f"{query_fn}{onstr} found {nmatches} candidates{matchstr}"

class NotFound(Exception):
    def __init__(self, query_fn: str, on: str=""):
        self.message = f"{query_fn}{' on ' if on else ''}{on} found no matches"


def arch_component(g: graph.LogSetGraphBase, label: str, within: str="") -> Qname:
    """ given a component label (and optional prefix for the system of interest), find the 
        qname of the component. Raises an exception if a unqiue component cannot be identified.
    """
    within_clause = ""
    if within:
        within_clause = f"""
            ?container rdfs:label "{within}" . 
            ?container logset:hasPart* ?thing .
        """ 
    sparql = f"""
        SELECT ?thing WHERE {{
            ?thing rdfs:label "{label}" .
            {within_clause}
        }}
    """
    logger.debug(f"running query: {sparql}")
    with g:
        result = g.query(sparql, initNs=dict(g.namespaces()))
        if len(result)==0:
            raise NotFound('arch_component', label)
        matches = [ g.qname(r[0]) for r in result ]
        if len(matches)>1:
            raise MultipleMatches('arch_component', len(matches), label, ', '.join(matches))
        return matches[0]


def arch_parents(g: graph.LogSetGraphBase, subject: Qname) -> t.Generator[t.Tuple[Qname,Qname,Qname], None, None]:
    """ given an architecture component, return a list of the "stack" of its parent/ancestor
        components (not necessarily in any particular order) 
    """
    sparql = f"""
        SELECT ?type ?parent ?thing WHERE {{
          ?thing a ?type .
          ?thing logset:hasPart* {subject} .
          ?parent logset:hasPart ?thing .
          OPTIONAL {{ ?parent logset:hasPart ?thing }} .
        }}
    """
    logger.debug(f"running query: {sparql}")
    with g:
        result = g.query(sparql, initNs=dict(g.namespaces()))
        for row in result:
            yield tuple(g.qname(i) for i in row)


def arch_parent(g: graph.LogSetGraphBase, subject: Qname, parent_type: Qname) -> Qname:
    """ return the parent/ancestor of type parent_type that contains subject """
    sparql = f""" 
        SELECT ?thing WHERE {{
            ?thing logset:hasPart* {subject} .
            ?thing a {parent_type} .
        }}
    """
    logger.info(f"sparql query: {sparql}")
    with g:
        result = g.query(sparql, initNs=dict(g.namespaces()))
        # what type is result? is it a generator? or a list? what do I need to do to 
        # correctly unpack it? (this is why I hate dynamic typing)
        # lets assume it's a list of tuples of uris (seems usually correct):
        if len(result) > 1:
            raise MultipleMatches('arch_parent', len(result), f"{subject},{parent_type}")
        if len(result) == 0:
            raise NotFound('arch_parent', f"{subject},{parent_type}")
        for row in result:
            return g.qname(row[0])
        #return g.qname(result[0][0])


def arch_coparts(g: graph.LogSetGraphBase, subject: Qname, parent_type: Qname, 
                 component_type: t.Optional[Qname]=None) -> t.Generator[t.Tuple, None, None]:
    """ given an architecture component, return a list of the related-child-components, 
        optionally just of a certain type
    """
    if component_type:
        t1, t2 = '', component_type # constrained
    else:
        t1, t2 = '?thingtype', '?thingtype' 

    sparql = f""" 
        SELECT ?thing {t1} WHERE {{
          ?parent a {parent_type} .
          ?parent logset:hasPart* {subject} .
          ?parent logset:hasPart* ?thing .
          ?thing a {t2} .
        }}
    """
    logger.debug(f"running query: {sparql}")
    with g:
        result = g.query(sparql, initNs=dict(g.namespaces()))
        for row in result:
            yield tuple(g.qname(i) for i in row)

def arch_neighbors(g: graph.LogSetGraphBase, subject: Qname) -> t.Generator[t.Tuple[Qname,Qname,Qname], None, None]:
    sparql = f"""
        SELECT ?blade ?link ?linktype WHERE {{
            {{
                SELECT ?link ?linktype WHERE {{
                    {subject} logset:hasPart*/logset:endPointOf ?link .
                    ?link a ?linktype .
                }} GROUP BY ?link
            }}
            ?blade a ddict:Blade .
            ?blade logset:hasPart*/logset:endPointOf ?link .
        }}
    """
    logger.debug(f"running query: {sparql}")
    with g:
        result = g.query(sparql, initNs=dict(g.namespaces()))
        for row in result:
            yield tuple(g.qname(i) for i in row)

