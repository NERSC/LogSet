#!/usr/bin/env python3
""" display information about locally-cached log metadata """

def setup_args(subparsers):
    myparser = subparsers.add_parser('info', help=__doc__)
    # takes no extra arguments

from .. import config
from .. import graph

import typing as t

def run(params: t.Dict[str,str]):
    print("running info command")

    print(f"inspecting {config.settings['persistence']['name']}")
    with graph.LogSetGraph() as g:
        contexts = [ c for c in g.contexts() ]
        print(f"found {len(g)} triples in {len(contexts)} subgraphs")
        print()

        for i, c in enumerate(contexts):
            print(f"subgraph {i}: {len(c)} triples from {str(c.identifier)}")

        for ns in g.namespaces():
            print(f"{ns[0]}: <{ns[1]}>")
