
```
../logs.py -v use mutrino-arch.ttl
```

    17:23 sleak@cori05:H/examples$ ../logs.py query 'SELECT ?node WHERE {
      ?slot logset:hasPart ?node .
      ?slot logset:hasPart ?aries .
      ?aries logset:hasPart ?tile .
      ?tile  logset:endPointOf mutrino:linkc0_0c0s10a0l23 .
    ?node a ?thing .
    ?thing rdfs:subClassOf* ddict:Node .
    }'
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c0_0c0s10n1'),)
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c0_0c0s10n2'),)
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c0_0c0s10n3'),)
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c0_0c0s10n0'),)
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c1_0c1s10n3'),)
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c1_0c1s10n0'),)
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c1_0c1s10n2'),)
    (rdflib.term.URIRef('https://portal.nersc.gov/project/m888/resilience/datasets/mutrino-arch#c1_0c1s10n1'),)




An example graph of a LogSet is:

.. code-block:: plantuml

@startuml

title logset as graph

package vocab <<rectangle>> {
  class LogSet <dcat:Dataset> {
    dct:temporal
  }
  class LogSeries
  class LogFormat
  class RecordFormat
  class DataSource
  class File
  File -u-|> DataSource
  LogSeries --> LogFormat : logFormat
  LogSeries --> RecordFormat : recordFormat
  DataSource -r-> LogSeries : isLogOf
  LogSet --> DataSource : hasLogData 
  LogSet --> DataSource : hasAnnotations 
}

package dict <<rectangle>> {
  class RegEx <rdfs:Literal>
  object "timeStampedLog:LogFormat" as timeStampedLog
  timeStampedLog .u.> LogFormat : is a
  object "filePerTimepoint:LogFormat" as filePerTimepoint
  filePerTimepoint .u.> LogFormat : is a 
  object console_log {
    filePattern: name_date
    seriesPattern: "console"
  }
  object consumer_log {
    filePattern: name_date
    seriesPattern: "console"
  }
  console_log .u.> LogSeries : is a 
  consumer_log .u.> LogSeries : is a 
  console_log -u-> timeStampedLog : logFormat
  consumer_log -u-> timeStampedLog : logFormat
}

object sample_data {
  dct:description "a partial sample of cori log data for testing logset tools"
}
sample_data .u.> LogSet : is a 

object "console-20170906" as console06
object "console-20170907" as console07
object "consumer-20170906" as consumer06
object "consumer-20170907" as consumer07

console06 ..> File : is a 

sample_data -u-> console06 : hasLogData
sample_data -u-> console07 : hasLogData
sample_data -u-> consumer06 : hasLogData
sample_data -u-> consumer07 : hasLogData

console06 -u-> console_log : isLogOf
console07 -u-> console_log : isLogOf
consumer06 -u-> consumer_log : isLogOf
consumer07 -u-> consumer_log : isLogOf

@enduml

.. end

