#!/usr/bin/env python3
from ExtractionRule import ExtractionRule
from SimpleSimplification import SimpleSimplification
from database import DatabaseConnection
import json
from jsonschema import validate

# Paths for area types JSON schema and document files
AREA_TYPES_DOCUMENT_FILE = "schema/area_types.json"
AREA_TYPES_SCHEMA_FILE = "schema/area_types_schema.json"

# Database settings
DATABASE_HOST = "localhost"
DATABASE_NAME = "gis"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = None

# JSON key names of the area type definition
JSON_KEY_TYPES_LIST = "types"
JSON_KEY_TYPE_NAME = "name"
JSON_KEY_TYPE_TABLE_NAME = "table_name"
JSON_KEY_TYPE_GEOMETRY_LIST = "geometries"
JSON_KEY_TYPE_CONDITIONS = "filter_condition"
JSON_KEY_TYPE_LABELS = "labels"
JSON_KEY_TYPE_SIMPLIFICATION = "simplification"
JSON_KEY_TYPE_ZOOM_MIN = "zoom_min"
JSON_KEY_TYPE_ZOOM_MAX = "zoom_max"

# Required queries for creating and preparing a result table
RESULT_TABLE_QUERIES = ["DROP TABLE IF EXISTS {0};",
                        """CREATE TABLE {0}
                        (
                            id INT NOT NULL,
                            geom GEOMETRY NOT NULL,
                            zoom INT DEFAULT 0,
                            geojson TEXT DEFAULT NULL,
                            CONSTRAINT {0}_unique_id UNIQUE (id, zoom)
                        );""",
                        "CREATE INDEX {0}_geom_index ON {0} USING GIST(geom);",
                        "CREATE INDEX {0}_zoom_index ON {0} (zoom);"]

# Supported zoom range
ZOOM_RANGE = range(0, 19)  # OSM default: range(0,19)

# Simplification algorithm to use
SIMPLIFICATION = SimpleSimplification()

database = None


def main():
    global database

    # Read area types from JSON file
    area_types = readAreaTypesFromFile()

    # Connect to database
    print(f"Connecting to database \"{DATABASE_NAME}\" at \"{DATABASE_HOST}\" as user \"{DATABASE_USER}\"...")
    database = DatabaseConnection(host=DATABASE_HOST, database=DATABASE_NAME, user=DATABASE_USER,
                                  password=DATABASE_PASSWORD)
    print("Successfully connected")

    # Iterate over all area types
    for type in area_types:
        extractAreaType(type)

    print("Simplification finished")
    print("Everything done.")

    database.disconnect()


def extractAreaType(area_type):
    global database

    name = area_type[JSON_KEY_TYPE_NAME]
    print(f"Next area type: \"{name}\"")

    table_name = area_type[JSON_KEY_TYPE_TABLE_NAME]
    print(f"Preparing table \"{table_name}\"...")
    createResultTable(database, table_name)
    print(f"Table prepared")

    # Create extraction rule
    print("Extracting geometries:")
    conditions = area_type[JSON_KEY_TYPE_CONDITIONS]
    extraction_rule = ExtractionRule(conditions)
    result = extraction_rule.extract(database)
    print(f"Extracted {len(result)} geometries")

    print("Preprocessing data...")

    do_simplification = area_type[JSON_KEY_TYPE_SIMPLIFICATION]
    zoom_min = area_type[JSON_KEY_TYPE_ZOOM_MIN]
    zoom_max = area_type[JSON_KEY_TYPE_ZOOM_MAX]

    zoom_range = range(zoom_min, zoom_max)

    # Iterate over all desired zoom levels
    for zoom in zoom_range:
        # Check if simplification is desired
        if do_simplification:
            processed_result = SIMPLIFICATION.simplify(constraint_points=[], geometries=result, zoom=zoom)
        else:
            processed_result = result

        # Write result to database
        writeGeometries(table_name, processed_result, zoom)

    print("Finished area type \"{name}\"")


def writeGeometries(table_name, geometries, zoom):
    global database

    for id, geometry in geometries.items():
        # Extend geometry for SRID
        geometry['crs'] = {
            'type': 'name',
            'properties': {
                'name': "EPSG:4326"
            }
        }
        geoJSON = json.dumps(geometry)
        database.query(f"""INSERT INTO {table_name} (id, geom, zoom, geojson)
        VALUES ({id}, ST_GeomFromGeoJSON('{geoJSON}'), {zoom}, '{geoJSON}')""")


def createResultTable(database, table_name):
    for query in RESULT_TABLE_QUERIES:
        database.query(query.format(table_name))


def readAreaTypesFromFile():
    # Read in area types document file
    print(f"Reading area types document file \"{AREA_TYPES_DOCUMENT_FILE}\"...")
    with open(AREA_TYPES_DOCUMENT_FILE) as document_file:
        area_types = json.load(document_file)

    # Read in area types schema file
    print(f"Reading area types schema file \"{AREA_TYPES_SCHEMA_FILE}\"...")
    with open(AREA_TYPES_SCHEMA_FILE) as schema_file:
        area_schema = json.load(schema_file)

        # Validate document against the schema
        print("Validating area types definition...")
        validate(instance=area_types, schema=area_schema)

    # Return area types list if everything went fine
    return area_types[JSON_KEY_TYPES_LIST]


if __name__ == '__main__':
    main()
