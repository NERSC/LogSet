#!/usr/bin/env python3

import graph
import logging
import shutil
import os

logger = logging.getLogger(__name__)

#@given('these background validity checks')
#def setup_validity_checks(context):
#    context.validity_checks = context.text.splitlines() #[row['check'] for row in context.table]

@then('we should have a valid graph')
def run_validity_tests(context):
    with context.graph as g:
        check_prefix_presense(context, "logset")
        check_prefix_presense(context, "ddict")
        check_number_of_subjects(context, 43)
        check_number_of_triples(context, 43)

@then('the graph should have a namespace called "{prefix}"')
def check_prefix_presense(context, prefix: str):
    for p,ns in context.graph.namespaces():
        if p==prefix:
            break
    else:
        raise Exception("no namespace called {prefix} in {list(context.graph.namespaces())}")

@then('the graph should have at least {num:d} subjects')
def check_number_of_subjects(context, num: int):
    #print("checking number of subjects")
    nsubjects = len(list(context.graph.subjects())) 
    logging.info("found {nsubjects} subjects")
    assert nsubjects >= num

@then('the graph should have at least {num:d} triples')
def check_number_of_triples(context, num: int):
    assert len(context.graph) >= num

@when('a graph is instantiated with {store} persistence')
def instantiate_graph(context, store:str):
    #print(f"called instantiate_graph with {store}")
    try:
        if store == 'no local':
            #print("no local store")
            context.graph = graph.LogSetGraph()
        else:
            path = os.sep.join([context.test_dir, context.test_db_name])
            #print(f"store is {store} at {path}")
            #print(f"creatign the graph with clobber={context.clobber}")
            context.graph = graph.LogSetGraph(persistence=store, path=path, 
                clobber=context.clobber)
        #print("made a graph")
        #print(context.graph)
    except Exception as exc:
        logging.warning(f"got an exception! {exc}")
        context.exception = exc
    except:
        logging.warning("got some other error")
        raise
    #else:
    #    logging.warning(f"made graph {context.graph}")


@then('{exception} should be raised')
def check_for_exception(context, exception):
    #logging.warning(f"checking if {type(context.exception).__name__} is {exception}")
    assert type(context.exception).__name__ == exception


@given('clobber is {clobber}')
def set_clobber(context, clobber: str):
    # clobber appears as a string, so we need to convert it
    context.clobber = clobber == 'True' 

import tempfile
@given('the {db_name} is {path_status}')
def ensure_path_has_chosen_status(context, db_name: str, path_status: str):
    context.test_db_name = db_name
    path = os.sep.join([context.test_dir, context.test_db_name])
    if path_status == 'available':
        # should have been setup by before_scenario
        assert os.path.isdir(context.test_dir)
        assert not os.path.exists(path)
    elif path_status == 'unreachable':
        shutil.rmtree(context.test_dir)
        assert not os.path.exists(context.test_dir)
    elif path_status == 'in_use':
        if not os.path.exists(path):
            with open(os.path, 'w') as f:
                f.write("something that is not turtle")
        assert(os.path.exists(path))
        assert os.path.exists(context.test_dir)

@given('a graph in {store} persistence called {name} that has these additional triples')
def setup_graph_with_data(context, store:str, name:str):
    path1 = os.sep.join([context.test_dir, "_extra_data.ttl"])
    with open(path1, 'w') as f:
        f.write(context.text)

    context.test_db_name = name
    path = os.sep.join([context.test_dir, context.test_db_name])
    new_graph = graph.LogSetGraph(persistence=store, path=path, create=True, clobber=True)
    with new_graph as g:
        g.extend(path1)



## this might be too ugly to rely on:
#@then('the graph should have {num:d} local namespaces')
#def check_local_namespace_count(context, num: int):
#    # local namespaces are ones actually in the graph, as distinct from ones
#    # referenced by the graph:
#    local_namespaces = { prefix:str(ns) for prefix,ns in context.graph.namespaces() 
#                         if str(ns) not in graph.external_namespaces }
#    # rdflib has a bug where namespaces with an empty prefix
#    # are not properly cleaned up, so we'll allow for it:
#    if '' in local_namespaces:
#        logging.warning(f"WARNING dangling empty prefix binding {local_namespaces['']}")
#        del(local_namespaces[''])
#    assert len(local_namespaces) == num
#

