#!/usr/bin/env python3
""" Node is a base for classes corresponding to owl:Classes in the 
    Graph. The intent is to provide a common interface for instantiating
    things based on results of a query 
"""

import sys
if sys.version_info < (3,5):
    raise Exception("Requires python 3.5+")

import logging
import re
from rdflib.term import Identifier, URIRef, Literal
from typing import Dict,Set,Union,List,TypeVar,Optional,ClassVar
from util import Context, MultiDict, ran_str, UI
import graph

NodeType = TypeVar('NodeType',bound='Node')
PropertyGetterDict = Dict[str, str] # predicate, name_of_getter
PropertyValue = Union[Identifier,'Node']
PropertyValues = Set[PropertyValue] #Union[Identifier,'Node']]
PropertyDict = Dict[str, PropertyValues]


class Node:
    """ A node in the global RDF graph """

    # what RDF class is this? (corresponds to "thing a class" in RDF). Note
    # that this is a string like "logset:ConcreteLog" - we won't know the 
    # URI until after the graph has been constructed
    # Should be concrete, ie vcard:Organization not vcard:Kind
    rdf_class: ClassVar[str] = ''       # eg "foaf:Organization"

    # certain node types are created as a specific class (eg foaf:Organization 
    # for Agent), but when querying the graph we need to find any subclass of 
    # some superclass (eg foaf:Agent for Agent). If that is the case, the 
    # Node class should specify the superclass with:
    rdf_superclass: ClassVar[str] = ''  # eg "foaf:Agent"

    # when adding a Node to the graph, triples for a certain set of properties
    # (based on the type of Node) are expected. These might be obtained by 
    # querying a file/source or asking the user or infering from context, etc.
    # Each class specifies the expected properties and how to obtain them via a
    # class-variable 'getters', which is a dict mapping a predicate (str) to 
    # the method (of self) that obtains it.
    # getter methods are called like:
    #   values:PropertyValues = self.getter(context:Context)
    getters: ClassVar[PropertyGetterDict] = {}
    # some predicates *must* be present, indicate these with:
    required_properties: ClassVar[Set[str]] = set()

    # to support finding known nodes of a given type, Node classes should
    # define a sparql query that returns rows from which a Node can be 
    # instantiated. This is done by mapping each row to the finder_fields
    # and passing the result as a PropertyDict to __init__ (see method known())
    finder_query:str = ''
    finder_fields:List[str] = []

    # for 'select' and 'multi_select' getters, what target class is being selected? 
    targets:Dict[str,NodeType] = {}  # eg 'dct:publisher': Agent

    # prompts for simple questions system can "ask" to get some properties:
    prompts:Dict[str,str] = {}    # eg 'dct:title': "Give the LogSet a title"

    # which property to use as a label? (this is useful because when defining
    # a new Thing and asking the user questions about it, it is helpful to
    # create the instance with a label that is included in the prompts. The
    # label generally corresponds with one of the properties of the Node, so
    # we require each subclass to indicate which property it will use
    label_property:str = None
    label_alternate = 'this'

    @property
    def graph(self):
        #logging.debug("getting graph: {0}".format(graph.Graph.the_graph))
        return graph.Graph.the_graph

    #def __init__(self, properties:PropertyDict = None) -> None: 
    def __init__(self, properties:MultiDict = None, **kwargs) -> None: 
        # lazy getting of uri is going to be common enough to just build it into the base class:
        self._uri: Optional[str] = None
        self._namespace: Optional[str] = None
        self._label: Optional[str] = None

        # eg "dct:title": set(Literal("my title"))
        self.properties = MultiDict(properties) 
        for key,val in kwargs.items():
            self.properties.add(key, val)

        if 'uri' in self.properties:
            self._uri = self.properties.one('uri')
            self.properties.remove('uri')

        if 'namespace' in self.properties:
            self._namespace = self.properties.one('namespace')
            self.properties.remove('namespace')

#        if properties is not None and 'uri' in properties:
#            logging.debug("setting uri from properties: {0}".format(properties['uri']))
#            #self._uri = properties.pop('uri')[0]
#            self._uri = properties.one('uri')
#            properties.remove('uri')
#
#        if properties is not None and 'namespace' in properties:
#            logging.debug("setting namespace from properties: {0}".format(properties['namespace']))
#            #self._uri = properties.pop('uri')[0]
#            self._namespace = properties.one('namespace')
#            properties.remove('namespace')

        # all attributes we have a getter for should have an
        # entry in properties, even if it is empty:
        for predicate in self.getters:
            if predicate not in self.properties:
                self.properties.add(predicate)

        # when adding a node to the graph and recursing into its properties, 
        # we want a mechanism to bypass adding nodes that are already in the
        # graph:
        self._in_graph = False

    @classmethod
    def instance(cls, uri):
        """ given the uri of a node, instantiate an object of this class based
            on the properties of that node in the graph
        """
        if not isinstance(uri, URIRef):
            uri = graph.geturi(uri)
        mdict = MultiDict(uri=[uri])
        preds = [ k for k in cls.getters.keys() ] # impose an order
        preds_by_uri = { graph.geturi(p):p for p in preds }
        for pred_uri,obj in self.graph.predicate_objects(uri):
            if pred_uri in preds_by_uri:
                mdict.add(preds_by_uri[pred_uri], obj)
            else:
                # its a property we're not prepared for, just include it as an Identifier
                mdict.add(pred_uri, obj)
        return cls(properties=mdict) 
        

    @classmethod
    def known(cls, filters:Dict[str,str]=dict()):
        """ generator-constructor over known nodes of a given type: """
        # TODO instead of sampling property values, use "order by" and a douple 
        # loop to actually get the full set of properties for a uri
        # (the general finder query is like:
        # select ?uri <other fields> <optional fields where {
        #    ?uri a <self.rdf_class> .
        #    ?uri <other predicate> <other variable> .
        #    optional {
        #       ?uri <other predicate> <other variable> .
        #    } } order by ?uri
        # then make a multi-dict of the properties
        # so:
        #  - first add a class var: required: list of required properties
        #
        #   # list of variables:
        #   nrequired = len(self.required)
        #   optionals = [ key for key in self.getters if key not in self.required ]
        #   ntotal = nrequired + len(optionals)
        #   required = [ '?v{:d}'.format(i) for i in range(nrequired) ]
        #   optional = [ '?v{:d}'.format(i) for i in range(nrequired,ntotal) ]
        #   query  = "SELECT ?uri " + ' '.join(self.required) + ' '.join(optionals)
        #   query += " WHERE { "
        #   if self.rdf_superclass is None:
        #       query += "   ?uri a {0} .".format(self.rdf_class)
        #   else:
        #       query += "   ?uri a ?type ."
        #       query += "   ?type rdfs:subClassOf* {0} .".format(self.rdf_superclass)
        #   for clause in zip(self.required, required):
        #       query += " ?uri {0} {1} . ".format(clause[0], clause[1])
        #   if noptional > 0:
        #       query += " OPTIONAL { "
        #       for clause in zip(optionals, optional):
        #           query += " ?uri {0} {1} . ".format(clause[0], clause[1])
        #       query += " } "
        #   query += " } ORDER BY ?uri "
        #   curr = None
        #   next = None
        #   for row in  Graph.graph.query(query):
        #       next = row[0] # the uri
        #       if next != curr: 
        #           mdict = Multidict(next)
        #           if curr is not None:
        #               yield cls(properties=mdict)
        #           curr = next
        #       # add each var to mdict
        #       for key,val in zip(required+optional,row):
        #           mdict.add(key, [val])
        #   yield cls(properties=mdict) # the last one
        #
        # or easier still: since we don't actually enforce that certain properties are 
        # required, make everything optional:
        # 
        # if filters has uris/rdflib identifiers, then to convert to str they need < > around it
        # but if they are a string like 'ddict:someThing' then they should stay as they are:
        as_str = lambda x: "<{0}>".format(str(x)) if isinstance(x,Identifier) else x
        logging.debug("filters has: {0}".format(filters))
        preds = [ k for k in cls.getters.keys() ] # impose an order
        qvars = [ '?v{:d}'.format(i) for i in range(len(preds)) ]
        query  = "SELECT ?uri {0} WHERE {{ ".format(' '.join(qvars))
        if cls.rdf_superclass is None:
            query += "?uri a {0} . ".format(cls.rdf_class)
        else:
            query += "?uri a ?type . "
            query += "?type rdfs:subClassOf* {0} . ".format(cls.rdf_superclass)
        for pred,var in zip(preds, qvars):
            if pred in filters:
                #query += "?uri {0} {1} . ".format(pred,str(filters[pred]))
                query += "?uri {0} {1} . ".format(pred,as_str(filters[pred]))
            else:
                query += "OPTIONAL {{ ?uri {0} {1} . }} ".format(pred,var)
        query += "} ORDER BY ?uri "
        logging.debug("query is: {0}".format(query))
        
        curr_uri = None
        next_uri = None
        mdict: MultiDict = None
        #for row in graph.Graph.the_graph.query(query):
        for row in graph.query(query):
            logging.debug("found {0}".format(str(row)))
            next_uri = row[0] # the uri
            if next_uri != curr_uri:
                if curr_uri is not None:
                    logging.debug("making a {0} with props {1}".format(cls.__name__, str(mdict)))
                    yield cls(properties=mdict)
                mdict = MultiDict(uri=[next_uri])
                curr_uri = next_uri
            # add each var to mdict
            for key,val in zip(preds, row[1:]):
                mdict.add(key, val)
        if mdict is not None:
            logging.debug("making a {0} with props {1}".format(cls.__name__, str(mdict)))
            yield cls(properties=mdict) # the last one
        else:
            logging.debug("no nodes of type {0} found".format(cls.__name__))
        
        #
        #if cls.finder_query is None:
        #    return
        #for row in Graph.graph.query(cls.finder_query):
        #    logging.info("found row:" + str(row))
        #    # each think in the row needs to be a list for MultiDict:
        #    lists = [ [r] for r in row ]
        #    props = dict(zip(cls.finder_fields, lists))
        #    logging.debug("making a {0} with props {1}".format(cls.__name__, str(props)))
        #    yield cls(properties=props)
            
    def get_values(self, predicate:str, context:Optional[Context]=None) -> PropertyValues:
        """ return a set of values for a property """
        if context is None:
            context = Context(predicate=predicate)
        logging.debug("looking for {0} in {1}".format(predicate, str(self.properties)))
        props = self.properties.get(predicate)
        if len(props)==0:
            logging.debug("calling a getter for {0}".format(predicate))
            getter = getattr(self, self.getters[predicate])
            logging.debug("got getter {0}, context {1}".format(getter, context))
            generator = (v for v in getter(context))
            self.properties.add(predicate, *generator)
            logging.debug("now {0} has: {1}".format(predicate, str(self.properties[predicate])))
        return self.properties[predicate]

    def get_one_value(self, predicate:str, context:Context=None) -> PropertyValue:
        values = self.get_values(predicate, context)
        if values is None or len(values)==0:
            return None
        else:
            return values.pop()

    #def label(self, context:Context=None) -> str:
    @property
    def label(self) -> str:
        """ when asking questions of the user, hinting at who is asking 
            is helpful. If the label should have more to it than the 
            content of the label property, then the subclass should 
            override this (eg, the subjectttype label is from
            'skos:prefLabel', but the logset label is "this logset {dct:title}"
        """
        #return self.properties.one(self.label_property, 'this')
        #return self.get_one_value(self.label_property, context) or 'this'
        # Note: this should not trigger getters, so we use self.properties
        # not self.get_one_value:
        #self._label = self.get_one_value(self.label_property) or self.label_alternate
        if self._label is None:
            candidates = self.properties[self.label_property]
            if len(candidates)>0:
                self._label = candidates.pop()
            else:
                self._label = self.label_alternate
        return self._label

    def __str__(self):
        # note that this should not trigger getters, so we use _uri not uri
        return "{0}: {1}".format(self.label, str(self._uri))


    @property
    def uri(self):
        # many subclasses will override this to lazily set a uri based on
        # the value of a property
        return self._uri

    @uri.setter 
    def uri(self,value):
        self._uri = value

    def add_to_graph(self, context:Context=None):
        if self._in_graph:
            logging.debug("already in graph, skipping")
            return

        if context is None:
            context = Context()

        # describe my properties first, so subclasses can use them to generate a helpful uri if necessary:
        # I think that to avoid loops we need to do all of the asking (the user)
        # before doing any of the adding to graph:
        triples = []
        context.push(node=self)
        for predicate in self.properties:
            context.push(predicate=predicate)
            # need to convert string eg foaf:name to an actual uri for adding
            # to graph:
            logging.debug("calling Graph.geturi on {0}".format(predicate))
            pred_uri = graph.geturi(predicate)
            logging.debug("calling get_values with {0}, {1}".format(str(predicate),str(context)))
            for v in self.get_values(predicate, context):
                if isinstance(v, Identifier):
                    triples.append( (self.uri, pred_uri, v) )
                elif isinstance(v, Node):
                    triples.append( (self.uri, pred_uri, v.uri) )
                else:
                    # I'm pretty sure this should never happen
                    raise Exception("oh oh! " + str(v) + " ... " + str(type(v)))
            context.pop(('predicate',))
        context.pop(('node',))
        for triple in triples:
            logging.debug("adding triple {0}".format(triple))
            self.graph.add( triple )

        # finally, describe me:
        rdf = graph.getns('rdf')
        myclass = graph.geturi(self.rdf_class)
        logging.info("adding me to graph: {0}, {1}, {2}".format(self.uri, str(rdf.type),str(myclass)))
        self.graph.add( (self.uri, rdf.type, myclass) )

        self._in_graph = True

    # some common getters:
    def skip(self, context:Context) -> PropertyValues:
        """ if it's not there, don't include it """
        logging.debug("calling skip wiht {0}".format(str(context)))
        return set()

    def abort(self, context:Context) -> None:
        """ if it's not there, something is badly wrong """
        logging.debug("calling abort wiht {0}".format(str(context)))
        predicate = str(context['predicate'])
        msg = "{0} {1} missing predicate {2}".format(self.rdf_class, 
                                            str(self.uri), predicate)
        raise Exception(msg)

    def ask(self, context:Context) -> PropertyValues:
        """ ask user for simple text descriptions (subclasses should override
            if needing something more complicated)
        """
        logging.debug("calling ask wiht {0}".format(str(context)))
        retval = set()
        predicate = context['predicate']
        logging.debug("asking about {0} (label property is {1}".format(str(predicate),str(self.label_property)))
        label = self.label_alternate if predicate == self.label_property else self.label
        prompt = self.prompts.get(predicate)
        if prompt is not None:
            insist = predicate in self.required_properties
            value = UI.ask(prompt.format(label), insist=insist)
            if value != '':
                #self._properties.add(pred, Literal(value))
                retval.add(Literal(value))
        return retval

    def truefalse(self, context:Context) -> PropertyValues:
        prompt = self.prompts.get(context['predicate'])
        choice = UI.truefalse(prompt)
        response = 'true' if choice else 'false'
        xsd = graph.getns('xsd')
        logging.debug("truefalse returning " + response)
        retval = set([Literal(response, datatype=xsd.boolean)])
        return retval

    def select(self, context:Context) -> PropertyValues:
        """ get a list of existing nodes of appropriate type (via the target
            class), and ask the user to select one, or create a new one
        """
        logging.debug("calling select with {0}".format(str(context)))
        predicate = context['predicate']
        label = self.label_alternate if predicate == self.label_property else self.label
        return self.select_from_known(context, label, multi=False)

    #@classmethod
    def multi_select(self, context:Context) -> PropertyValues:
        logging.debug("calling multi_select with {0}".format(str(context)))
        predicate = context['predicate']
        label = self.label_alternate if predicate == self.label_property else self.label
        return self.select_from_known(context, label)

    @classmethod
    def select_from_known(cls, context:Context=Context(), label=None, multi=True, 
                          allow_create=True, filters:Dict[str,str]=dict()) -> PropertyValues:
        """ classmethod select getter ..."""
        retval = set()
        predicate = context.get('predicate')
        target_cls = cls.targets.get(predicate, cls)
        known = list(target_cls.known(filters))

        if label is None:
            label = target_cls.__name__

        if multi:
            default_prompt  = "Please select one or more {0} "
            default_prompt += "(space-separated{1} or empty when done) "
            #ui_method = UI.multi_select
        else:
            default_prompt = "Please select a {0}{1}"
            #ui_method = UI.select

        prompt_new = ", or (n)ew " if allow_create else ""
        additional = ['n'] if allow_create else []

        prompt = (context.get('prompt') or
                  cls.prompts.get(predicate) or
                  default_prompt).format(label,prompt_new)

        if multi:
            selection = UI.multi_select(prompt, known, *additional) 
        else:
            selection = [ UI.select(prompt, known, *additional) ]
        
        while True:
            # loop so user can create multiple new entries
            if len(selection)==0:
                break
            # for multi, but with single it is same logic:
            for choice in selection:
                if allow_create and str(choice).lower() == 'n':
                    # now it gets giddyingly recursive, make a new target_cls Node 
                    # and add that:
                    classname = target_cls.__name__
                    label = UI.ask("please give the new {0} a label: ".format(classname))
                    props = {target_cls.label_property: [label]}
                    new = target_cls(properties=props) 
                    new.add_to_graph(context)
                    uri = new.uri
                else:
                    logging.info(f"got choice {choice} from selection {selection}")
                    #obj = known[choice]
                    obj = choice
                    uri = obj.uri 
                retval.add(uri)
            selection = UI.multi_select("more? ", known, 'n') if multi else []
            #selection = ui_method("more? ", known, 'n') if multi else []
        return retval


    def make_uri(self, prop, namespace):
        """ make a candidate uri that is human-readable if possible based on 
            the value of a selected property. If that property is not set, or
            the uri would clash with one that already exists, add some 
            random characters
        """
        # make an rdf-friendly name:
        try:
            name = re.sub('^[^A-Za-z]+|\W','',self.properties.one(prop))
        except KeyError:
            name = ran_str(8)

        # does it exist already?
        while existing in self.graph.predicate_objects(namespace[name]):
            # yep, choose a new name by adding some random characters to the end
            name = '{0}_{1}'.format(name, ran_str(4))

#        if len(name)==0:
#            name = ran_str(8)
#        else:
#            # does it exist already?
#            logging.info("makeing a uri in namespace {0}".format(namespace))
#            for existing in self.graph.predicate_objects(namespace[name]):
#                # yep, better choose a new name
#                name = '{0}_{1}'.format(name, ran_str(4))
#                break
#        logging.info("makeuri returning {0}".format(name))
        return namespace[name] 


#    @classmethod
#    def find_or_create(cls, context:Context=None, allow_create=True):
#        """ either find and return an existing Node, or create a new one """
#        addendum = ", or (n)ew" if allow_create else ""
#        ui_args = ['n'] if allow_create else []
#        predicate = context['predicate']
#        prompt = "Please select a {0}{1}: ".format(predicate, addendum)
#        known = list(self.known())
#        choice = UI.select(prompt, known, *ui_args)
#        if allow_create and str(choice).lower() == 'n':
#            obj = cls()
#            obj.add_to_graph(context)
#        else:
#            obj = known[choice]
#        return obj
#
#
#    def delegate(self, context:Context) -> PropertyValues:
#        """ create a predicate-specific object (the "delegate") and allow
#            it to 
#        """
#        # delegate to a predicate-specific class to find-and-add a suitable entry:
#        delegate = self.delegates[context['predicate']].find_or_create(context)
#        return set([delegate.uri])
#        #delegate = self.delegates[context['predicate']]()
#        #delegate.add_to_graph(context)

#    def __init__(self, uri:URIRef = None, 
#                 namespace:rdflib.Namespace = None,
#                 properties:PropertyDict = None) -> None: 
#        """ if a uri is provided, namespace is ignored, otherwise a namespace
#            must be provided to generate a unique uri in
#        """    
#        if uri is None:
#            assert namespace is not None
#            uri = namespace[ran_str(8)]
#        self.uri = uri
#        # do we want to get namespace too?
#        #self.namespace = rdflib.Namespace(uri[:cut])
#
#        # give subclasses a method to initialize private variables
#        # to None, etc, without needing to replicate __init__
#        self._init()
#
#        # eg "dct:title": set(Literal("my title"))
#        self.properties = MultiDict(properties) 
#
#        # all attributes we have a getter for should have an
#        # entry in properties:
#        for predicate in self.getters:
#            if predicate not in self.properties:
#                self.properties.add(predicate)
#            
#    def _init(self):
#        """ subclasses should override this (if desired) """
#        pass
