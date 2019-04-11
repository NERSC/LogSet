#!/usr/bin/env python3
""" import logset data from urls to local cache """

def setup_args(subparsers):
    myparser = subparsers.add_parser('use', help=__doc__)
    myparser.add_argument('urls', metavar='<url> ..',
        help="path or url to ingest", action='append')

import typing as t

import graph

def run(params: t.Dict[str,str]):

    with graph.LogSetGraph() as g:
        g.extend(*params['urls'])

