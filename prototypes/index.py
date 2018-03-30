#!/usr/bin/env python3

import sys
# system python 3 on Cori is broken so user will need to load a
# python module, which will be 3.6+ anyway, so we'll take advantage
# of some of python's modern features:
print(sys.version_info)
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

sys.path.append('/global/homes/s/sleak/Monitoring/Resilience/LogSet/src')
import LogsGraph
import rdflib

import re

# each new file in the index needs a unique iri:
import random, string
def ran_str(len):
    " produce a string of random letters, of a given length "
    return ''.join([random.choice(string.ascii_lowercase) for i in range(len)])

if __name__ == '__main__':

    # concrete first tool: given a path and optionally some urls with
    # dictionaries etc to include, walk the path for files and guide the user 
    # through creating an index for this dataset (included an expanded 
    # dictionary if required)

    #import logging
    #logger = logging.getLogger()
    #logger.setLevel(logging.DEBUG)

    usage = sys.argv[0] + " <path> [<url> <url> ...]\n"
    usage += "eg:\n"
    sampledir = "/global/cscratch1/sd/sleak/Resilience/corismw-sample-p0/p0-20170906t151820"
    sampleurl = "file:///global/homes/s/sleak/Monitoring/Resilience/LogSet/examples"
    usage += sys.argv[0] + " {0} {1} {2}\n".format(sampledir, sampleurl+'/nersc.ttl', 
                                                   sampleurl+'/cray-dict.ttl')
    if len(sys.argv) <= 1:
        print(usage)
        sys.exit(2)
    path = sys.argv[1]

    # TODO get the baseuri from options
    baseuri = "cori.nersc.gov:{}/".format(sys.argv[1]) 

    graph = LogsGraph.construct(*sys.argv[2:], spider=True)

    # What filepatterns do we recognize?
    patterns = {} # tag: regex
    query = '''SELECT ?tag ?regex WHERE {
                ?id a dict:FilenamePattern .
                ?id dict:tag ?tag .
                ?id dict:regex ?regex .
            }'''
    for row in graph.query(query):
        patterns[str(row[0])] = str(row[1])
    print(patterns)

    # and the LogSeries they correspond to:
    logseries = {} # filepattern: (regex, logseries, logformat, mediatype)
    query = '''SELECT ?filepattern ?logseries ?logfmt ?mediatype WHERE {
                    ?logseries a logset:LogSeries .
                    ?logseries logset:logFormatInfo ?filepattern .
                    ?logseries logset:logFormat ?logfmt .
                    OPTIONAL { ?logfmt dcat:mediaType ?mediatype } .
                    FILTER regex(?filepattern, "^filepattern=") .
            }'''
    tagpattern = re.compile('<\w+>')
    for row in graph.query(query):
        filepattern = str(row[0]).partition('=')[2]
        # filepattern may contain tags to convert to regexs: 
        for tag in tagpattern.findall(filepattern):
            filepattern = filepattern.replace(tag, patterns[tag])
            print (tag)
            print (patterns[tag])
            print (filepattern)
        regex = re.compile(filepattern)
        series = row[1]
        logfmt = row[2]
        mediatype = str(row[3])
        print("got filepattern: {}".format(filepattern))
        print("got regex: {}".format(regex))
        #print("got logseries: {}".format(series))
        #print("got logfmt: {}".format(logfmt))
        #print("got mediatype: {}".format(mediatype))
        logseries[filepattern] = (regex, series, logfmt, mediatype) 
    print(sorted(logseries, key=len, reverse=True))

    # make a new graph for this index, with its own namespace 
    # TODO get the namespace from command-line options:
    ns = rdflib.Namespace("http://example.org/myindex#")
    newindex = rdflib.ConjunctiveGraph()
    newindex.namespace_manager.bind("my_index", ns)

    import os
    baselen = len(path)+1
    remaining = set([(base[baselen:],f) for base, d, files in os.walk(path) for f in files])
    indexed = set()
    todo = set(logseries.keys())
    todo.add("") # empty string will be processed last, ensured we look for files 
                 # if/after there are no more patterns to try
    print("{} files remaining".format(len(remaining)))

    # some nodes we will need when added files to the graph:
    concretelog = LogsGraph.get("logset","ConcreteLog")
    isinstanceof = LogsGraph.get("logset","isInstanceOf")
    dcat =  rdflib.Namespace(LogsGraph.getns('dcat'))
    

    while len(todo) > 0:
        for p in sorted(todo, key=len, reverse=True):
            if p=="":
                break
            print("indexing files matching {}".format(p))
            regex = logseries[p][0]
            series = logseries[p][1]
            logfmt = logseries[p][2]
            matching = set(filter(lambda x: regex.match(x[1]), remaining))
            # should get confirmation from user before removing from remaining
            # now create an entry in the new graph for this file
            for m in matching:
                id = ran_str(8)
                newindex.add( (ns[id], rdflib.RDF.type, concretelog) )
                #print( dcat['downloadURL'])
                #print(m)
                #print(rdflib.URIRef(baseuri + m))
                newindex.add( (ns[id], dcat['downloadURL'], rdflib.URIRef(baseuri + m[-1])) )
                newindex.add( (ns[id], isinstanceof, series) )
                # TODO: have to get the temporal info
            remaining -= matching
            print("{} files remaining".format(len(remaining)))
            indexed.add(p)
            todo.remove(p)
            print("{} patterns indexed".format(len(indexed)))
        print("TODO looks for files not matching any pattern")
        break

    out = newindex.serialize(format='n3').decode('ascii')
    for line in out.splitlines()[:40]:
        print(line)
    for line in out.splitlines()[-40:]:
        print(line)
#
#    import os
#    baselen = len(path)+1
#    count=1
#    for d,f in [(base[baselen:],file) for base, dir, files in os.walk(path) for file in files]:
#        print((d,f))
#        count+=1
#        if count>10: break
        # algorithm will be:
        # - compare the filename against each of the known patterns
        # ask the user which (or none) of the matching patterns this file corresponds to
        # (maybe print the first few lines of the file, if it is text, or the type otherwise
        # as a hint)
        # the user can select a logseries, or "something new" (then give info on new series),
        # or "skip file", "skip pattern", "ignore pattern (skip all such)"
        # if we have a new series to create, define it via a template, add it to the graph in
        # a "mydict" namespace
        # add file to index in a "newindex" namespace
        # call on appropriate handler class to guess info about the file (so handler class 
        # needs to register itself and support and "index(new_item)" call 
        
        

