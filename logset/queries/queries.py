#!/usr/bin/env python3
""" sample/handy queries on a logset graph """

# note that all labels will have _ not -
q = """
SELECT ?node WHERE {
  ?slot logset:hasPart ?node .
  ?slot logset:hasPart ?aries .
  ?aries logset:hasPart ?tile .
  ?tile a craydict:Ptile .
  ?tile rdfs:label "c5_1c1s8a0l54" .
}
"""

from .. import graph
import rdflib.namespace as ns

import typing as t
Qname = str # a string like prefix:name

class MultipleMatchWarning(Exception):
    def __init__(self, query_fn: str, nmatches: int, on: str=""):
        self.message = f"{query_fn}{' on ' if on else ''}{on} found {nmatches} matches"

def arch_parent(g: graph.LogSetGraphBase, subject: Qname, parent_type: Qname) -> Qname:
    """ return the parent/ancestor of type parent_type that contains subject """
    sparql = f""" 
        SELECT ?thing WHERE {{
            ?thing logset:hasPart* {subject} .
            ?thing a {parent_type} .
        }}
    """
    with g:
        result = g.query(sparql, initNs=dict(g.namespaces()))
        # what type is result? is it a generator? or a list? what do I need to do to 
        # correctly unpack it? (this is why I hate dynamic typing)
        # lets assume it's a list of tuples of uris:
        if len(result) != 1:
            raise MultipleMatchWarning(arch_parent, len(result), f"{subject},{parent_type}")
        return g.qname(result[0][0])

# 16:45 sleak@cori04:H/LogSet$ ../logs.py query "
#$prefs
#SELECT ?thing ?thingtype ?tiletype WHERE {
#  $tile logset:endPointOf ?link .
#  ?thing logset:endPointOf ?link .
#  ?thing a ?thingtype .
#  $tile a ?tiletype .
#}"
#16:48 sleak@cori04:H/LogSet$ tile="mutrino:c0_0c1s10a0l50"
#16:49 sleak@cori04:H/LogSet$ tile="mutrino:c0_0c1s11a0l36"
#16:49 sleak@cori04:H/LogSet$ prefs="PREFIX craydict: <file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples/cray-dict#> PREFIX edison: <file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples/edison-arch#> PREFIX mutrino:<file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples/mutrino-arch#>"

#16:49 sleak@cori04:H/LogSet$ ../logs.py query "
#$prefs
#SELECT ?thing WHERE {
#  ?toplevel logset:hasPart* mutrino:c0_0c1s11a0l05 .
#  ?toplevel a ddict:Chassis .
#  ?toplevel logset:hasPart* ?thing .
#  ?thing a* ?typeofthing .
#?typeofthing rdfs:subClassOf* ddict:Node .
#}"
#16:49 sleak@cori04:H/LogSet$ ../logs.py query "
#$prefs
#SELECT ?thing WHERE {
#  ?thing logset:hasPart* mutrino:c0_0c1s11a0l05 .
#?thing a ddict:Chassis .
#}"

