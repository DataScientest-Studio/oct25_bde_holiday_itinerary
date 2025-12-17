CALL gds.graph.exists('city-road-graph') YIELD exists
WITH exists
WHERE NOT exists

CALL gds.graph.project(
  'city-road-graph',
  'City',
  {
    ROAD_TO: {
      type: 'ROAD_TO',
      orientation: 'UNDIRECTED',
      properties: 'km'
    }
  }
)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount;
