Feature: cataloging a set of logs

    As a site engineer
    I want to catalog collections of log data
    So that I can find logs relevant to an event of component I am investigating

    @backlog
    Scenario: describing the contents of a Cray p0 directory
        Given a Cray p0 directory
        And some system information
        When the p0 directory is catalogued
        Then each of the files will be described in the graph



