import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

#_logFormatTypes = None # dict of  name: class

from util import FileInfo, MultiDict, Context
from typing import Set
import os
from LogFormatType import LogFormatType
from ConcreteLog import ConcreteLog
#import handlers
from rdflib.term import Literal
from handlers import UnsupportedLogFormatHandler

class FileBasedLogFormatType(LogFormatType):
    rdf_class = "logset:LogFormatType"
    rdf_superclass = "logset:LogFormatType"
    handler = None

    def catalog(self, candidates:Set[FileInfo], context:Context) -> Set[FileInfo]:
        filepatterns = context['filepatterns']
        matching = set()
        for regex in filepatterns:
            logging.info("filepattern: {0}: {1}".format(regex,regex.pattern))
            logging.info("{0:d} candidates".format(len(candidates)))
            logging.info("candidates: {0}".format(candidates))
            logging.info("after filtering: " + str(filter(lambda x: regex.match(x.filename),candidates)))
            matching |= set(filter(lambda x: regex.match(x.filename),candidates))

        # args for the LogFormatType that will handle the actual file/source:
        handler_args = { 'rdf_class':  context['logFormatType'], 
                         'fmtinfo':    context['formatinfo']
                       }
                       #  'properties': self.properties
        #context.push(handler_factory=handlers.factory)
        context.push(handler_args=handler_args)

        # hmm, everything the ConcreteLog infers, we can just pass as properties:
        common_properties = MultiDict()  
        common_properties.add('logset:isInstanceOf', context['logseries_uri'])
        common_properties.add('dcat:accessURL', context['dcat:accessURL'])
        common_properties.add_values('logset:subject', context['subjects'])
        common_properties.add('namespace', context['namespace'])
        logging.info("logset for concretelog has: {0}".format(context['logset']))

        # in most cases we are looking file-by-file .. FilePerTimepoint
        # can override this default behavior
        for f in matching:
            #context.push(label=f.filename)
            #context.push({'dcat:downloadURL': f.relpath + os.sep + f.filename})
            properties = MultiDict(common_properties)  
            properties.add('rdfs:label', Literal(f.filename))
            relpath = (f.relpath + os.sep + f.filename).lstrip(os.sep)
            properties.add('dcat:downloadURL', Literal(relpath))
            logging.info("properties for concretelog has: {0}".format(properties))

            handler_args['target_url'] = os.sep.join(f) # full local path
            log = ConcreteLog(properties=properties)
            logging.info("adding log to graph: {0}".format(log))
            try:
                log.add_to_graph(context)
            except UnsupportedLogFormatHandler as err:
                logging.warn("logformat {0} not implemented".format(err))

            properties.remove('rdfs:label')
            properties.remove('dcat:downloadURL')
        context.pop(('handler_args',))
        #context.pop('handler_factory')

        return candidates-matching


