import logging
import sys
logging.debug(str(sys.version_info))
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    raise Exception("Requires python 3.5+, try module load python/3.6-anaconda-4.4")

#_logFormatTypes = None # dict of  name: class

from util import FileInfo, MultiDict, Context
from typing import Set
import os
from Node import Node


from rdflib.term import BNode, Literal
class LogFormatInfoKey(Node):
    rdf_class = "logset:LogFormatInfo"
    getters = {
        'dct:description':    'ask'
              }
    required_properties = set(['logset:fmtInfoKey'])
    prompts = {
        'logset:fmtInfoKey':  "Variable {0} represents? ",
        'dct:description':    "What information should the value of {0} provide? "
              }
    label_property = 'logset:fmtInfoKey'
    label_alternate = "this formatinfo"

    @property
    def uri(self) -> str:
        if self._uri is None:
            self._uri = BNode()
        return self._uri

class LogFormatType(Node):
    rdf_class = "logset:LogFormatType"

    getters = {
        'rdfs:label':        'ask',
        'dct:description':   'ask',
        'dcat:mediaType':    'ask',
        'logset:dataSource': 'select',
        'logset:fmtInfoKey': 'ask'
              }
    required_properties = set(['logset:dataSource'])
    # prompts for simple questions system can "ask" to get some properties:
    prompts = {
        'rdfs:label':      "Give {0} a short label: ",
        'dct:description': "Please enter short description for {0}: ",
        'dcat:mediaType':  "What MIME type does {0} correspond to? "
              }
    #targets = {
    #    'logset:DataSource': DataSource
    #            }
    label_property = 'rdfs:label'
    label_alternate = 'this logformattype'


