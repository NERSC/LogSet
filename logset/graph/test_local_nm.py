#!/usr/bin/env python3

import pytest
from . import local_nm

@pytest.fixture
def make_nm():
    import rdflib
    g = rdflib.Graph()
    return local_nm.LocalNM(g)

import hypothesis as hyp
import hypothesis.strategies as st

sample_urls = [
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'https://www.w3.org/2000/01/rdf-schema#',
    'http://purl.org/dc/terms/',
    'file://a/local/file',
    'file:///an/absolute/path',
    'file:///an/absolute/path.ttl',
    'file://../up/one/',
    'something.ttl',
]

sample_prefixes = [
    # should correspond to sample_urls above
    'rdf',
    'rdfs',
    'dct',
    'file',
    'path',
    'pathttl',
    'relpath',
    'something',
]

urls = st.sampled_from(sample_urls)
n3s = st.sampled_from( f"<{u}>" for u in sample_urls )
urirefs = st.sampled_from( rdflib.URIRef(u) for u in sample_urls )
namespaces = st.sampled_from( rdflib.Namespace(u) for u in sample_urls )

prefixes = st.sampled_from(sample_prefixes)

#prefixes = 
#(and corresponding prefixes)
#
#    ('rdf', 
#
#namespace = rdflib.URIRef(six.text_type(namespace))

#@hyp.given(text())
#def test_decode_inverts_encode(s):
#    assert decode(encode(s)) == s

@hyp.given(prefixes, urls)
def test_bind(prefix, url):
    print(f"testing with {prefix}, {url}")
    #def bind(self, prefix, namespace, override=True, replace=False):

