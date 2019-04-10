Feature: locally persisting and using a graph

    As a developer
    I want to easily open and use a graph with the logset vocabulary etc
    So that I can build the capabilities of the tool around it

    Scenario: not using local persistence
        When a graph is instantiated with no local persistence
        Then we should have a valid graph


    Scenario Outline: correctly creating a local persistence
        Given clobber is <clobber>
        And the <db name> is <path status>
        When a graph is instantiated with <store> persistence
        Then we should have a valid graph

        Examples:
            | store     | clobber | db name  | path status |
            | Sleepycat | True    | kv.db    | available   |
            | Sleepycat | True    | kv.db    | in use      |
            | Sleepycat | False   | kv.db    | available   |
            | SQLite3   | True    | sql.db   | available   |
            | SQLite3   | True    | sql.db   | in use      |
            | SQLite3   | False   | sql.db   | available   |
            | Turtle    | True    | file.ttl | available   |
            | Turtle    | True    | file.ttl | in use      |
            | Turtle    | False   | file.ttl | available   |


    Scenario Outline: incorrectly using the local persistence
        Given clobber is <clobber>
        And the <db name> is <path status>
        When a graph is instantiated with <store> persistence
        Then <exception> should be raised

        Examples:
            | store     | clobber | db name  | path status | exception         |
            | Sleepycat | True    | kv.db    | unreachable | FileNotFoundError |
            | Sleepycat | False   | kv.db    | unreachable | FileNotFoundError |
            | SQLite3   | True    | sql.db   | unreachable | OperationalError  |
            | SQLite3   | False   | sql.db   | unreachable | OperationalError  |
            | Turtle    | True    | file.ttl | unreachable | FileNotFoundError |
            | Turtle    | False   | file.ttl | unreachable | FileNotFoundError |
# FIXME all three methods clobber an existing file!
#            | Sleepycat | False   | kv.db    | in use      | FileExistsError   |
#            | SQLite3   | False   | sql.db   | in use      | FileExistsError   |
#            | Turtle    | False   | file.ttl | in use      | FileExistsError   |


    @wip
    Scenario Outline: opening an existing local graph
        Given a graph in <store> persistence called <name> that has these additional triples:
            """
            @prefix logset: <http://portal.nersc.gov/project/mpccc/sleak/resilience/datasets/logset#> .
            @prefix ddict: <http://portal.nersc.gov/project/mpccc/sleak/resilience/datasets/logset#> .
            @prefix : <http://example.com/logset_test#> .

            :c1_0 a ddict:Cabinet ;
                logset:hasPart :c1_0c0;
                logset:hasPart :c1_0c1;
                logset:hasPart :c1_0c2;
                .

            :c4_0 a ddict:Cabinet ;
                logset:hasPart :c4_0c1;
                logset:hasPart :c4_0c2;
                logset:hasPart :c4_0c0;
                .
            """
        And clobber is False
        When a graph is instantiated with <store> persistence
        Then we should have a valid graph
#        And it should have a subject "c4_0"

        Examples:
            | store     | name     |
            | Turtle    | file.ttl |
            | SQLite3   | test.db  |
# Sleepycat seems to have a race condition and fails when opening an existing db, about 
# 85% of the time:
#            | Sleepycat | test.db  |

