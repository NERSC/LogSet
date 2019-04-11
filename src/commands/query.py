#!/usr/bin/env python3
""" run a sparql query against the metadata graph """

def setup_args(subparsers):
    myparser = subparsers.add_parser('query', help=__doc__)
    myparser.add_argument('query', metavar='<query>',
        help="sparql query (use quotes to delimit)")

import typing as t

import graph

def run(params: t.Dict[str,str]):

    print("got query:")
    print(params['query'])
    with graph.LogSetGraph() as g:
        for row in g.query(params['query']):
            print(row)

