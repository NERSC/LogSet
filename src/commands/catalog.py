#!/usr/bin/env python3

import logging

from commands import Command, ArgDetails
import rdflib
from rdflib.term import Literal
import graph
from util import Context, FileInfo, UI
#from graph import LogSet, Subject, DataSource, graph
from LogSet import LogSet
from Subject import Subject
#from DataSource import DataSource
#from LogSeries import LogSeries
import DataSource 
import os



class Catalog(Command):
    command = "catalog"
    purpose = "catalog a directory tree that holds log data"
    usage = "catalog <directory>"

    # TODO eventually: add the ability to catalog other sources.
    # Eg via sacct calls, or curl requests
    # Those may need handlers and LogSeries and LogFormatTypes 
    # written specifically for them

    _args = [ ArgDetails(
                '-c', '--catalog', 1, False, "url of catalog to update",
                "-c ./example-cat.ttl" ),
              ArgDetails(
                '-n', '--namespace', 1, True, "namespace for this new dataset",
                "-n http://example.org/myindex#" ),
              ArgDetails(
                '-d', '--dir', 1, True, "directory to scan for log files to catalog",
                "-d /global/cscratch1/sd/sleak/Resilience/corismw-sample-p0/p0-20170906t151820")
            ]
            # TODO some sources are not a local directory, eg when cataloging 
            # data accessible via curl, will do other things to access it
            # or when cataloging slurm stuff via sacct

    def execute(self, args):
        topdir = args.dir[0]
        # namespace should have at least 1 '/' and should end in '#'.
        # the label for the LogSet itself will be the text between 
        # the last '/' and the '#', and the LogSet will be written to
        # a file called {label}.ttl:
        nstart = args.namespace[0].rfind('/')+1
        nend = -1 if args.namespace[0][-1]=='#' else None
        base = args.namespace[0][:nstart]
        name = args.namespace[0][nstart:nend]
        ns = rdflib.Namespace(base+name+'#')
        uri = ns[name]
        #logging.info("logset uri is {0}".format(uri))
        catalog = args.catalog[0] if args.catalog else None

        # flatten additional urls into a single list:
        urls = [u for urllist in args.url for u in urllist]
        #urls = args.url[0] or []
        logging.debug("got args: {0}".format(str(args)))
        logging.debug("got urls: {0}".format(str(urls)))

        fname = '{0}.ttl'.format(name)
        if os.path.exists(fname):
            msg  = "{0} already exists, please move it or request ".format(fname)
            msg +=  "a different namespace and try again"
            raise Exception(msg)

        g = graph.construct(*urls, spider=True)
        #print("the graph is now: {0}".format(graph.Graph.the_graph))
        newindex = LogSet(uri=uri)
        logging.debug("created a Logset newindex: {0}".format(str(newindex)))
        newindex.add_to_graph()

        # ask user what (high-level) subjects the logs are about, to help in 
        # guessing subjects of concretelogs
        subjects = set()
        prompt = "Please indicate the (high-level) subjects of these logs, or some (n)ew ones: "
        while len(subjects)==0:
            context = Context(prompt=prompt)
            subjects = Subject.select_from_known(context)
            context.pop(('prompt',))
            prompt = "please indicate at least 1 subject!"

        guess = newindex.get_one_value('dcat:landingPage') or "http://example.com"
        guess += "/logs.tar.gz"
        prompt =  "What URL can these logs be accessed via? \n"
        prompt += "(eg, " + guess + "\n"
        # FIXME: should this actually be a URIRef?
        accessURL = Literal(UI.ask(prompt, guess))

        # new context for cataloging the actual data sources:
        context = Context(logset=newindex, subjects=subjects, namespace=newindex.namespace)
        context.push({'dcat:accessURL': accessURL})
        datasource = DataSource.factory('ddict:files')
        datasource.catalog(topdir, context)

        ## series to search for logs of:
        #todo = set(LogSeries.known())
        #done = set()
        #logging.debug("todo has: {0}".format([', '.join(str(i)) for i in todo])))
        ## move this into the logformattype:
        ## files to finding matching series for:
        #baselen = len(topdir)+1
        #remaining = set([ FileInfo(topdir, path[baselen:], f) 
        #                  for path, d, files in os.walk(topdir) for f in files ])
        #while len(todo) > 0:
        #    logseries = todo.pop()
        #    remaining = logseries.catalog(remaining, context)
        #    done.add(pattern)
        #    todo.remove(pattern)
        #    if len(todo)==0:
        #        # we need to come up with more logseries
        #        break # for now


        # write the new index:
        subgraph = graph.subgraph(newindex.prefix)
        with open(fname, 'w') as f:
            f.write(subgraph.serialize(format='n3').decode('ascii'))
        # TODO make this less fragile
        # write any new entities and localdict too:
        try:
            subgraph = graph.subgraph('new_entities')
            with open('new_entities.ttl', 'w') as f:
                f.write(subgraph.serialize(format='n3').decode('ascii'))
        except KeyError:
            # no new entities to write
            pass
        try:
            subgraph = graph.subgraph('localdict')
            with open('localdict.ttl', 'w') as f:
                f.write(subgraph.serialize(format='n3').decode('ascii'))
        except KeyError:
            # no new entities to write
            pass


