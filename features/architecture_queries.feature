Feature: querying the network architecture

    As a researcher or site engineer
    With an observation of an event impacting a component
    I want to identify the set of components affecting this one
    So that I can trace the event back to its root cause
    By looking for events on related components

    @backlog
    Scenario: finding components that impact this one
        A tool can iterate between querying for components that impact any in a
        given list, and sieving components by whether some events were observed on
        them (eg by looking for annotations), to search for the root cause of that
        event
        Given a graph containing the description of a system
        And a set of components on which some fault was observed
        When the graph is queried for immediate upstream components
        Then a list is produced of components whose behavior can impact these components

    @backlog
    Scenario: finding components impacted by this one
        TODO we might want to select a "level" too, eg give me the node, not every 
        component of it
        Given a graph containing the description of a system
        And a component on which a fault was observed
        When the graph is queried for immediate downstream components
        Then a list is produced of components that might have been impacted


