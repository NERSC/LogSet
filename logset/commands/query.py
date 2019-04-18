#!/usr/bin/env python3
""" run a sparql query against the metadata graph """

import logging as logger
#logger = logging.getLogger(__name__)

def setup_args(subparsers):
    myparser = subparsers.add_parser('query', help=__doc__)
    myparser.add_argument('query', metavar='<query>',
        help="sparql query (use quotes to delimit)")

import typing as t
from .. import graph

def run(params: t.Dict[str,str]):

    logger.info("got query:")
    logger.info(params['query'])
    with graph.LogSetGraph() as g:
        for row in g.query(params['query']):
            print(row)

