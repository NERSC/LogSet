#!/usr/bin/env python3

import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

from rdflib.term import BNode, Literal
from util import Context, MultiDict
import handlers
from graph import getns
from Node import Node, PropertyValues
import dateutil.parser


class Temporal(Node):
    rdf_class = "dct:PeriodOfTime"
    getters = {
        'logset:startDate': 'inspect',
        'logset:endDate': 'inspect',
              }
    required_properties = set(getters.keys())

    @property
    def uri(self) -> str:
        if self._uri is None:
            self._uri = BNode()
        return self._uri

    def inspect(self, context:Context) -> PropertyValues:
        retval = set()
        predicate = context['predicate']
        handler = context['handler']
        xsd = getns('xsd')
        if predicate == 'logset:startDate':
            retval.add(Literal(handler.t_earliest, datatype=xsd.dateTime))
        elif predicate == 'logset:endDate':
            # note if it is a live source, enddate should be None
            retval.add(Literal(handler.t_latest, datatype=xsd.dateTime))
        return retval


class ConcreteLog(Node):
    rdf_class = "logset:ConcreteLog"
    getters = {
        'rdfs:label':              'infer',
        'logset:isInstanceOf':     'infer',
        'dcat:downloadURL':        'infer',
        'dcat:accessURL':          'infer',
        'logset:subject':          'infer',
        'dct:temporal':            'inspect',
        'dcat:byteSize':           'inspect',
        'logset:recordCount':      'inspect',
        'logset:estRecordCount':   'inspect',
        'logset:estRecordsPerDay': 'inspect',
              }
    required_properties = set(['rdfs:label', 'logset:isInstanceOf', 
                               'logset:subject', 'dct:temporal'])
    label_property:str = 'rdfs:label'
    label_alternate = 'this'

    def __init__(self, properties:MultiDict = None) -> None: 
        logging.debug("concretelog created with {0}".format(properties))
        super().__init__(properties=properties)
        self.handler = None

    @property
    def uri(self):
        if self._uri is None:
            logging.debug("concretelog making a uri from {0}".format(self.properties))
            ns = self._namespace
            self._uri = self.make_uri(self.label_property, ns)
        return self._uri

    # this might be redundant - can get them from properties passed in:
    def infer(self, context:Context) -> PropertyValues:
        """ get properties from context """
        logging.warn("in concretelog .infer with predicate {0}".format(context['predicate']))
        predicate = context['predicate']
        retval = set()
        if predicate == 'rdfs:label':
            retval.add(Literal(context['label']))
        elif predicate == 'logset:isInstanceOf':
            retval.add(context['logseries'].uri)
        elif predicate in ('dcat:downloadURL','dcat:accessURL'):
            retval.add(context[predicate].uri)
        elif predicate == 'logset:subject':
            retval = set(context['subjects'])
        return retval

    def inspect(self, context:Context) -> PropertyValues:
        """ get properties by calling on the handler """
        xsd = getns('xsd')
        if self.handler is None:
            #handler_factory = context['handler_factory']
            handler_args = context['handler_args'] # dict of kwargs
            logging.debug("in inspect, cntext has: {0}".format(context))
            logging.debug("in inspect, handler_args has: {0}".format(handler_args))
            self.handler = handlers.factory(**handler_args)
            #self.handler = handler_factory(**handler_args)
        retval = set()
        predicate = context['predicate']
        if predicate == 'dct:temporal':
            context.push(handler=self.handler, predicate=predicate)
            t = Temporal()
            t.add_to_graph(context)
            context.pop(('handler','predicate'))
            retval.add(t.uri)
        elif predicate == 'dcat:byteSize':
            value = self.handler.size
            xsd = getns('xsd')
            retval.add(Literal(value, datatype=xsd.integer))
        elif predicate == 'logset:recordCount':
            if self.handler.num_records is not None:
                retval.add(Literal(self.handler.num_records, datatype=xsd.integer))
        elif predicate == 'logset:estRecordCount':
            if self.handler.num_records is not None:
                retval.add(Literal(self.handler.num_records, datatype=xsd.integer))
            else:
                buf = list(self.handler.get_slice(limit=10))
                avg = sum([len(entry) for entry in buf]) / len(buf)
                guess = self.handler.size / avg
                retval.add(Literal(guess, datatype=xsd.integer))
        elif predicate == 'logset:estRecordsPerDay':
            # get timespan from handler, convert to days, etc
            # the handler stores the timespan just as text, so need to convert
            t_earliest = dateutil.parser.parse(self.handler.t_earliest)
            t_latest = dateutil.parser.parse(self.handler.t_latest)
            days = (t_latest - t_earliest).total_seconds()/86400
            nrecs = self.get_one_value('logset:recordCount') or \
                    self.get_one_value('logset:estRecordCount')
            nrecs = int(float(str(nrecs))) # sorry
            nrecs_per_day = int(nrecs/days)
            retval.add(Literal(nrecs_per_day, datatype=xsd.integer))
        return retval

    def add_to_graph(self, context:Context=None):
        super().add_to_graph(context)
        dcat = graph.getns('dcat')
        self.graph.add( (context['logset'], dcat.distribution, self.uri) )






