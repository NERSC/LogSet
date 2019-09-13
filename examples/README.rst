
```
../logs.py -v use new_mutrino.ttl
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



some queries:
 - given a component, get the "stack" of its parents
SELECT ?thing ?type ?parent WHERE {
  ?thing a ?type .
  ?thing logset:hasPart* $component .
  ?parent logset:hasPart ?thing .
  OPTIONAL { ?parent logset:hasPart ?thing } .
}

- given a component, get the ancestor of a specific type:
SELECT ?thing WHERE {
 ?thing a $type .
 ?thing logset:hasPart* $component .
}

- given a component, get the children/components within its parent of a specific type
 ("related"? or "coparts"?)
SELECT ?thing ?thingtype WHERE {
  ?parent a $type .
  ?parent logset:hasPart* $component .
  ?parent logset:hasPart* ?thing .
  ?thing a ?thingtype .
}

- same, but constrained to things of a given thingtype:
SELECT ?thing WHERE {
  ?parent a $type .
  ?parent logset:hasPart* $component .
  ?parent logset:hasPart* ?thing .
  ?thing a $thingtype .
}

- given a thing containing one or more endpoints, get whatever is at the other end:
SELECT ?endpoint ?link ?linktype WHERE {
  ?thisend logset:endPointOf ?link .
  ?endpoint logset:endPointOf ?link .
  ?link a ?linktype .
  $thing logset:hasPart* ?thisend .
}

- this works eventually, but is way too slow - must be doing something n^2:
SELECT ?blade ?link ?linktype WHERE {
?thisend logset:endPointOf ?link .
?endpoint logset:endPointOf ?link .
?link a ?linktype .
mutrino:c0_0c0s3a0 logset:hasPart* ?thisend .
?blade logset:hasPart* ?endpoint .
?blade a ddict:Blade .
}

this is vastly faster, but still too slow:
 SELECT ?blade ?link ?linktype WHERE {
 ?blade a ddict:Blade .
 ?blade logset:hasPart*/logset:endPointOf ?link .
 ?link a ?linktype .
 mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
 }
real	10m8.272s
user	9m46.920s
sys	0m15.191s

SELECT ?blade ?link ?linktype WHERE {
  {
    SELECT ?link ?linktype WHERE {
      mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
      ?link a ?linktype . 
    } GROUP BY ?link
  }
  ?blade a ddict:Blade .
  ?blade logset:hasPart*/logset:endPointOf ?link .
}
real	7m39.794s
user	7m24.406s
sys	0m11.268s



(and, i actually want to get the nodes..)
(can I use filters or nested subquery to reduce the graph?)

SELECT ?blade ?link ?linktype WHERE {
  ?blade a ddict:Blade .
  ?blade logset:hasPart*/logset:endPointOf ?link .
  {
    SELECT ?link sample(?linktype) as ?linktype WHERE {
      mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
      ?link a ?linktype .
    } GROUP BY ?link
  }
}

# this version returns all links in the system (not just the relevent ones)
SELECT ?blade ?link ?linktype WHERE {
  ?blade a ddict:Blade .
  ?blade logset:hasPart*/logset:endPointOf ?link .
  ?link a ?linktype .
  {
    SELECT ?link WHERE {
      mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
    } GROUP BY ?link
  }
}


SELECT DISTINCT ?blade WHERE {
  {
    SELECT ?link WHERE {
      mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
    } GROUP BY ?link
  }
  { 
    SELECT ?blade WHERE {
      ?blade a ddict:Blade .
      ?blade logset:hasPart*/logset:endPointOf ?link .
    } GROUP BY ?blade
  }
}

SELECT ?blade ?link ?linktype WHERE {
  {
    SELECT ?link ?linktype WHERE {
      mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link . ?link a ?linktype .
    } GROUP BY ?link
  }
  {
    SELECT ?blade WHERE {
      ?blade a ddict:Blade .
      ?blade logset:hasPart*/logset:endPointOf ?link .
    } GROUP BY ?blade
  }
}
real	7m50.792s
user	7m35.512s
sys	0m11.993s


SELECT ?node WHERE {
  {
    SELECT ?link WHERE {
      mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
    } GROUP BY ?link
  } 
  {
    SELECT ?blade WHERE {
      ?blade a ddict:Blade .
      ?blade logset:hasPart*/logset:endPointOf ?link .
    } GROUP BY ?blade
  } 
  ?node a ddict:ComputeNode .
  ?blade logset:hasPart* ?node .
}
real	8m20.594s
user	8m2.922s
sys	0m14.249s
but returns duplicates

SELECT ?node WHERE {
  {
      SELECT DISTINCT ?blade WHERE {
        {
          SELECT ?link WHERE {
            mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
          } GROUP BY ?link
        }
        ?blade a ddict:Blade .
        ?blade logset:hasPart*/logset:endPointOf ?link .
      }
  }
  ?node a ddict:ComputeNode .
  ?blade logset:hasPart ?node .
}
real	7m26.062s
user	7m11.602s
sys	0m11.184s
returns just the nodes, once each. (aaa)

SELECT ?node ?linktype WHERE {
  {
      SELECT DISTINCT ?blade ?linktype WHERE {
        {
          SELECT ?link ?linktype WHERE {
            mutrino:c0_0c0s3a0 logset:hasPart*/logset:endPointOf ?link .
            ?link a ?linktype .
          } GROUP BY ?link
        }
        ?blade a ddict:Blade .
        ?blade logset:hasPart*/logset:endPointOf ?link .
      }
  }
  ?node a ddict:ComputeNode .
  ?blade logset:hasPart ?node .
}
real	7m51.160s
user	7m35.804s
sys	0m11.932s
but returns duplicates of the subject blade, one for each link tpye







SELECT ?blade WHERE {
   ?blade a ddict:Blade .
   ?endpoint ^logset:hasPart* ?blade .
   {
     SELECT ?endpoint WHERE {
       mutrino:c0_0c0s3a0 logset:h\zasPart*/logset:endPointOf ?link .
       ?endpoint logset:endPointOf ?link .
     } GROUP BY ?endpoint
   }
}



SELECT ?neighbor ?linktype WHERE {
  $part logset:hasPart* ?endpoint .
  ?endpoint logset:endPointOf ?link .
  ?link a ?linktype .
  ?linktype rdfs:subClassOf* logset:Link .
  ?neighbor logset:endPointOf ?link .
}

- cray-specific: given some part of an aries router, get all the nodes that are within
  a single hop:
SELECT ?neighbor ?linktype WHERE {
  ?blade a ddict:Blade .
  ?blade logset:hasPart cray:ariesRouter .
  ?aries logset:hasPart* $ariespart .
  ?blade logset:hasPart* ?thisend .
  ?thisend logset:endPointOf ?link .
  otherblade


- given something within a blade, return a list of nodes/servers within 1 hop
  ("neighbors") (this is a bit cray-specific)
SELECT ?server ?servertype ?linktype WHERE {
  ?blade a ddict:Blade .
  ?blade logset:hasPart* $component .
  ?server a ?servertype .
  ?servertype rdfs:subClassOf* ddict:Server .
  ?blade logset:hasPart* ?thisend .
  ?thisend logset:endPointOf ?link .
  ?otherend logset:endPointOf ?link .

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

