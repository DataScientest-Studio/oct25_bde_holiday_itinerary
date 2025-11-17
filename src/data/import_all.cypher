LOAD CSV WITH HEADERS FROM "file:///france_poi.csv" AS row
WITH row, split(row.types, ',') AS typesList

MERGE (poi:Poi {id: row.id})
  ON CREATE SET
    poi.label                  = row.label,
    poi.comment                = row.comment,
    poi.description            = row.description,
    poi.types                  = typesList,
    poi.homepage               = row.homepage,
    poi.city                   = row.city,
    poi.postal_code            = row.postal_code,
    poi.street                 = row.street,
    poi.x                      = toFloat(row.lat),
    poi.y                      = toFloat(row.long),
    poi.additional_information = row.additional_information;

CALL apoc.cypher.runFile("file:///cities_roadto.cypher");