from ExtractionRule import ExtractionRule
from SimpleSimplification import SimpleSimplification
from database import DatabaseConnection
import json

# Database settings
DATABASE_HOST = "localhost"
DATABASE_NAME = "gis"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = None

# Database table that holds the simplified data
TABLE_RESULT_NAME = "simplified"

TABLE_RESULT_QUERIES = [f"DROP TABLE IF EXISTS {TABLE_RESULT_NAME};",
                        f"""CREATE TABLE {TABLE_RESULT_NAME}
                        (
                            id INT NOT NULL,
                            geom GEOMETRY NOT NULL,
                            zoom INT DEFAULT 0,
                            geojson TEXT DEFAULT NULL,
                            CONSTRAINT unique_id UNIQUE (id, zoom)
                        );""",
                        f"CREATE INDEX geom_index ON {TABLE_RESULT_NAME} USING GIST(geom);",
                        f"CREATE INDEX zoom_index ON {TABLE_RESULT_NAME} (zoom);"]

ZOOM_RANGE = range(0, 19)  # default OSM: range(0,19)
SIMPLIFICATION = SimpleSimplification()
EXTRACT_BUNDESLAENDER = ExtractionRule("admin_level='8'")


def main():
    # Connect to database
    print(f"Connecting to database \"{DATABASE_NAME}\" at \"{DATABASE_HOST}\" as user \"{DATABASE_USER}\"...")
    database = DatabaseConnection(host=DATABASE_HOST, database=DATABASE_NAME, user=DATABASE_USER,
                                  password=DATABASE_PASSWORD)
    print("Successfully connected")

    print(f"Preparing table \"{TABLE_RESULT_NAME}\"...")
    createResultTable(database)
    print(f"Table prepared")

    # Extract bundeslaender from database
    print("Extracting bundeslaender...")
    result = EXTRACT_BUNDESLAENDER.extract(database)
    print(f"Extracted {len(result)} geometries")

    print("Proceeding with simplification...")
    # Iterate over all desired zoom levels
    for zoom in ZOOM_RANGE:
        # Simplify the result for the current zoom level
        simplified = SIMPLIFICATION.simplify(constraint_points=[], geometries=result, zoom=zoom)
        writeGeometries(database, simplified, zoom)

    print("Simplification finished")
    print("Everything done.")

    database.disconnect()


def writeGeometries(database, geometries, zoom):
    for id, geometry in geometries.items():
        # Extend geometry for SRID
        geometry['crs'] = {
            'type': 'name',
            'properties': {
                'name': "EPSG:4326"
            }
        }
        geoJSON = json.dumps(geometry)
        database.query(f"""INSERT INTO {TABLE_RESULT_NAME} (id, geom, zoom, geojson)
        VALUES ({id}, ST_GeomFromGeoJSON('{geoJSON}'), {zoom}, '{geoJSON}')""")


def createResultTable(database):
    for query in TABLE_RESULT_QUERIES:
        database.query(query)


if __name__ == '__main__':
    main()
