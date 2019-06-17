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
