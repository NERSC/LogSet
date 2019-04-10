#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import logging
logging.basicConfig(level=logging.DEBUG)

import behave

def before_all(context):
    os.makedirs('tests', exist_ok=True)

import tempfile
def before_scenario(context, scenario):
    featurename = scenario.filename.rpartition(os.sep)[2].replace('.feature','')
    prefix = f"{featurename}-{scenario.line}."
    context.test_dir = tempfile.mkdtemp(prefix=prefix, dir='_tests')

import shutil
def after_scenario(context, scenario):
    if scenario.status == 'passed':
        print(f"removing {context.test_dir}")
        shutil.rmtree(context.test_dir)
    else:
        # if a failed or skipped scenario left an empty directory, remove it (it's just
        # mess), but if there is anything inside, leave it there so I can post-mortem
        try:
            print(f"removing {context.test_dir}")
            os.rmdir(context.test_dir)
        except:
            pass

#import graph
#@behave.fixture
#def persistence(context, persistence: str='', *args, **kwargs):
#    with graph.LogSetGraph(persistence, *args, **kwargs) as context.graph:
#        yield
#
#def before_tag(context, tag: str):
#    if tag.startswith("fixture.persistence"):
#        _, sep, persistence = tag.rpartition('.')
#        use_fixture(persistence, context, persistence=persistence)
#
#def before_feature(context, feature):
#    if feature.name != 'locally persisting and using a graph':
#        # for most tests we'll use an in-memory-only graph:
#        use_fixture(persistence, context)
