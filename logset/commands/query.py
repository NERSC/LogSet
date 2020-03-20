#!/usr/bin/env python3
""" run a sparql query against the metadata graph """

import logging as logger
#logger = logging.getLogger(__name__)

def setup_args(subparsers):
    myparser = subparsers.add_parser('query', help=__doc__)
    myparser.add_argument('--sparql', '-s', nargs=1, metavar='<sparql-query>',
        help="sparql query (use quotes to delimit)")
    myparser.add_argument('--parent', '-p', nargs=1, metavar='<parent-type>',
        help="find nearest component of <parent-type> containing the subject component")
    myparser.add_argument('--containers', '-c', action='store_true', 
        help="find all components that directly or indirectly contain thie subject")
    myparser.add_argument('subject')

import typing as t
from .. import graph
from .. import queries

def run(params: t.Dict[str,str]):

    gmem = graph.LogSetGraph(persistence='Memory', source=graph.LogSetGraph())
    ## copy the graph to an in-memory one for faster querying:
    #gfile = graph.LogSetGraph()
    #gmem = graph.LogSetGraph(persistence='Memory')
    #gmem.addN(gfile.quads())

    readable = lambda d: '\n'.join(str(i) for i in d.items()) 

    logger.debug(params)
    if params['sparql']:
        logger.info("got sparql query:")
        logger.info(params['sparql'][0])
#        with graph.LogSetGraph() as g:
        with gmem as g:
            nsdict = {p:ns for p,ns in g.namespace_manager.namespaces()}
            #print(f"querying with ns manager {g.namespace_manager}")
            #print(f"with namespaces {readable(nsdict)}")
            for row in g.query(params['sparql'][0], initNs=nsdict):
                try: 
                    print([g.qname(term) for term in row if term])
                    #print([term for term in row if term])
                except:
                    #print(f"ERROR printing {row}")
                    for t in row:
                        try:
                            print(g.qname(t))
                        except:
                            logger.warning(f"Error finding qname in {t}")
                    raise
    elif params['containers']:
        #for type_, parent, thing in queries.arch_parents(graph.LogSetGraph(), params['subject']):
        for type_, parent, thing in queries.arch_parents(gmem, params['subject']):
            print(f"{type_:20}  {parent:20}  holds {thing}")
    elif params['parent']:
        #parent = queries.arch_parent(graph.LogSetGraph(), params['subject'],params['parent'][0])
        parent = queries.arch_parent(gmem, params['subject'],params['parent'][0])
        print(f"{parent}")
        


