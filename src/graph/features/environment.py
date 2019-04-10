#!/usr/bin/env python3

# assumption here is that we are running behave from the top-level directory
# (ie above src)

#import sys
#sys.path.append('src')

import logging
logging.basicConfig(level=logging.DEBUG)

import behave

#import graph
#@behave.fixture
#def persistence(context, persistence: str='', *args, **kwargs):
#    with graph.LogSetGraph(persistence, *args, **kwargs) as context.graph:
#        yield

import os

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
        #shutil.rmtree(context.test_dir)
    else:
        # if the failed or skipped scenario left an empty directory, remove it (it's 
        # just mess), but if there is anything inside, leave it there so I can 
        # post-mortem
        try:
            print(f"removing {context.test_dir}")
            os.rmdir(context.test_dir)
        except:
            pass

def before_tag(context, tag: str):
    if tag.startswith("fixture.persistence"):
        _, sep, persistence = tag.rpartition('.')
        use_fixture(persistence, context, persistence=persistence)

def before_feature(context, feature):
    if feature.name != 'locally persisting and using a graph':
        # for most tests we'll use an in-memory-only graph:
        use_fixture(persistence, context)
