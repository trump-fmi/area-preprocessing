import json

TARGET_PROJECTION = 4326
TABLES_LINES = ['planet_osm_line', 'planet_osm_polygon']

class ExtractionRule:
    def __init__(self, conditions):
        self.conditions = conditions

    def extract(self, database):
        # Dict for all extracted geometries
        geometriesDict = {}

        # Iterate over all point tables
        for table in TABLES_LINES:

            # Build query
            query = f"SELECT osm_id, ST_AsGEOJSON(ST_Transform(ST_ForceRHR(way), {TARGET_PROJECTION})) FROM {table} WHERE {self.conditions}"

            # Execute query
            result = database.queryForResult(query)

            # Iterate over all result rows
            for row in result:
                # Sanity check
                if len(row) < 1: continue

                id = row[0]
                geoJSON = row[1]

                geometry = json.loads(geoJSON)
                geometriesDict[id] = geometry

        # Return resulting list of geometries
        return geometriesDict
