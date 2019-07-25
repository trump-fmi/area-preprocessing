import json

TARGET_PROJECTION = 4326


class ExtractionRule:
    def __init__(self, conditions):
        self.conditions = conditions

    def extract(self, database, source_tables):
        # Dict for all extracted geometries
        geometries_dict = {}

        # Dict for all extracted names
        names_dict = {}

        # Iterate over all point tables
        for table in source_tables:

            print(f"Extracting from table \"{table}\"...")

            # Build query
            query = f"SELECT osm_id, name, ST_AsGEOJSON(ST_Transform(way, {TARGET_PROJECTION})) FROM {table} WHERE {self.conditions}"

            # Execute query
            result = database.queryForResult(query)

            # Iterate over all result rows
            for row in result:
                # Sanity check
                if len(row) < 1: continue

                # Extract relevant data from query result
                id = row[0]
                name = row[1]
                geoJSON = row[2]

                # Add sanitized name to name dict if available
                if name is not None:
                    name = name.replace("'", "").replace("\"", "").replace("\n", "")
                    names_dict[id] = name

                # Convert JSON geometry to object
                geoObject = json.loads(geoJSON)

                # Add geometry to geometry dict
                geometries_dict[id] = geoObject

        # Return resulting list of geometries
        return geometries_dict, names_dict
