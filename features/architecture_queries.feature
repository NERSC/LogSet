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
        Given a graph containing the description of a system, read from <url>
        And a set of components on which some fault was observed
        When the graph is queried for immediate upstream components
        Then we get a list of the following components
            """
            """

    @backlog
    Scenario: finding components of a given type that are impacted by this one
        For example, if we know that an Aries tile has a fault, we might want to find
        which jobs are affected. For that we will need the affected node list, so we 
        need to trace up from the tile to the blade, and then get the nodes comprising 
        that blade
        Given a graph containing the description of a system, read from <url>
        And that a fault was observed on component <component>
        And that we are interested in subject of type <subject type>
        When the graph is queried for downstream components
        Then we get a list of the following components
            """
            """

    @backlog
    Scenario: finding components within n network hops of this one
        For example, if we know that a certain aries router or tile has a problem, 
        finding the directly affected (0 hops) nodes and indirectly affected (especially
        1 hop away) nodes might be valuable
        Given a graph containing the description of a system, read from <url>
        And that a fault was observed on component <component>
        And that we are interested in subject of type <subject type>
        And we want to scan across up to <n> network hops
        When the graph is queried
        Then we get a list of the following components
            """
            """
