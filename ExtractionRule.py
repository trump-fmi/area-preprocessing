import json

TARGET_PROJECTION = 4326

class ExtractionRule:
    def __init__(self, conditions):
        self.conditions = conditions

    def extract(self, database, source_tables):
        # Dict for all extracted geometries
        geometriesDict = {}

        # Iterate over all point tables
        for table in source_tables:

            print(f"Extracting from table \"{table}\"...")

            # Build query
            query = f"SELECT osm_id, ST_AsGEOJSON(ST_Transform(way, {TARGET_PROJECTION})) FROM {table} WHERE {self.conditions}"

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
