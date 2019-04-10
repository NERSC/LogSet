Feature: describing a system or subsystem

    As a site engineer
    I want to describe my facility and systems with RDF
    By manually indicating systems and relationships
    And by ingesting information from tool output
    So that I can trace events through related components to find root causes and 
    likely other victims

    @external
    Scenario: ingesting the network architecture of a cluster from rtr output
        Given a LogSet graph
        And a turtle file describing the cluster network architecture
        When the turtle file is added to the graph
        Then the graph will contain the cluster and many networked components

