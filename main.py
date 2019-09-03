#!/usr/bin/env python3
from ExtractionRule import ExtractionRule
from NoSimplification import NoSimplification
from SimpleSimplification import SimpleSimplification
from BlackBoxSimplification import BlackBoxSimplification
from database import DatabaseConnection
import json
from jsonschema import validate
import gc

# File paths for area types JSON schema and document files
AREA_TYPES_DOCUMENT_FILE = "../area-types/area_types.json"
AREA_TYPES_SCHEMA_FILE = "../area-types/area_types_schema.json"

# Database settings
DATABASE_HOST = "localhost"
DATABASE_NAME = "gis"
DATABASE_USER = "osm"
DATABASE_PASSWORD = None

# Maps geometry types to source tables in the database
SOURCE_TABLES = {
    "nodes": "planet_osm_point",
    "lines": "planet_osm_line",
    "polygons": "planet_osm_polygon"
}

# JSON key names of the area types definition
JSON_KEY_TYPES_LIST = "types"
JSON_KEY_TYPE_NAME = "name"
JSON_KEY_TYPE_SOURCES = "sources"
JSON_KEY_TYPE_SOURCE_LABELS = "labels"
JSON_KEY_TYPE_SOURCE_LABELS_ARCED = "arced"
JSON_KEY_TYPE_SOURCE_LABELS_ZOOM_MIN = "zoom_min"
JSON_KEY_TYPE_SOURCE_LABELS_ZOOM_MAX = "zoom_max"
JSON_KEY_TYPE_SOURCE_TABLE_NAME = "table_name"
JSON_KEY_TYPE_SOURCE_FILTERS = "filter_parameters"
JSON_KEY_TYPE_SOURCE_SIMPLIFICATION = "simplification"
JSON_KEY_TYPE_SOURCE_ZOOM_MIN = "zoom_min"
JSON_KEY_TYPE_SOURCE_ZOOM_MAX = "zoom_max"

# Required queries for preparing a result table
TABLE_PRE_QUERIES = ["DROP TABLE IF EXISTS {0};",
                     """CREATE TABLE {0}
                     (
                         id INT NOT NULL,
                         geom GEOMETRY NOT NULL,
                         zoom INT DEFAULT 0,
                         name TEXT DEFAULT NULL,
                         geojson TEXT DEFAULT NULL,
                         CONSTRAINT {0}_unique_id UNIQUE (id, zoom)
                     );"""]

# Required queries for postprocessing a result table
TABLE_POST_QUERIES = ["CREATE INDEX {0}_geom_index ON {0} USING GIST(geom);",
                      "CREATE INDEX {0}_zoom_index ON {0} (zoom);"
                      "CLUSTER {0}_geom_index ON {0};"]

# Supported zoom range
ZOOM_RANGE = range(19, -1, -1)  # OSM default: range(0,19)

# Simplification algorithm to use
# SIMPLIFICATION = BlackBoxSimplification()
SIMPLIFICATION = NoSimplification()

# Number of geometries to write within one database query
WRITE_BATCH_SIZE = 100

# Database instance
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
    for area_type in area_types:
        # Get area type name
        area_type_name = str(area_type[JSON_KEY_TYPE_NAME])

        # Get area type sources
        area_type_sources = area_type[JSON_KEY_TYPE_SOURCES]

        print(f"Next area type: \"{area_type_name}\"")

        # Iterate over all sources of this area type and invoke their extraction
        for area_type_source in area_type_sources:
            extractAreaTypeSource(area_type_source)

        print(f"Finished area type \"{area_type_name}\"")

    print("Simplification finished")
    print("Everything done.")

    database.disconnect()


def extractAreaTypeSource(area_type_source):
    global database

    # Extract properties of interest from area type source definition
    table_name = str(area_type_source[JSON_KEY_TYPE_SOURCE_TABLE_NAME])
    filter_conditions_list = area_type_source[JSON_KEY_TYPE_SOURCE_FILTERS]
    simplify_geometries = bool(area_type_source[JSON_KEY_TYPE_SOURCE_SIMPLIFICATION])
    zoom_min = float(area_type_source[JSON_KEY_TYPE_SOURCE_ZOOM_MIN])
    zoom_max = float(area_type_source[JSON_KEY_TYPE_SOURCE_ZOOM_MAX])

    print(f"Preparing table \"{table_name}\"...")
    prepare_table(database, table_name)
    print(f"Table prepared")

    # Create extraction rule and use it to extract geometries and names
    print("Extracting geometries...")
    extraction_rule = ExtractionRule(filter_conditions_list)
    geometries_dict, names_dict = extraction_rule.extract()
    print(f"Extracted {len(geometries_dict)} geometries and {len(names_dict)} names")

    print("Preprocessing data...")

    # Iterate over all desired zoom levels
    for zoom in ZOOM_RANGE:
        # Check if zoom is within zoom range for this area type
        if (zoom < zoom_min) or (zoom >= zoom_max): continue

        print(f"Simplifying geometries for zoom level {zoom}...")

        # Check if simplification is desired
        if simplify_geometries:
            processed_result = SIMPLIFICATION.simplify(constraint_points=[], geometries=geometries_dict, zoom=zoom)
        else:
            processed_result = geometries_dict

        # Write result to database
        print(f"Writing simplified geometries for zoom level {zoom} to database...")
        write_geometries(table_name, processed_result, names_dict, zoom)

        # Force garbage collection
        gc.collect()

    print(f"Postprocessing table \"{table_name}\"...")
    postprocess_table(database, table_name)


def write_geometries(table_name, geometries, names, zoom):
    global database

    geometry_items = list(geometries.items())

    for i in range(0, len(geometry_items), WRITE_BATCH_SIZE):
        chunk_list = geometry_items[i:i + WRITE_BATCH_SIZE]

        queryValues = []

        for id, geometry in chunk_list:
            # Extend geometry for SRID
            geometry['crs'] = {
                'type': 'name',
                'properties': {
                    'name': "EPSG:4326"
                }
            }

            # Stringify GeoJSON in a compact way
            geo_json = json.dumps(geometry, separators=(',', ':'))

            # Check if name available
            name = "NULL"
            if id in names:
                name = "'" + names[id] + "'"

            value = f"({id}, ST_Envelope(ST_GeomFromGeoJSON('{geo_json}')), {zoom}, {name}, '{geo_json}')"
            queryValues.append(value)

        # Build query string
        query_string = f"INSERT INTO {table_name} (id, geom, zoom, name, geojson) VALUES " + (
            ",".join(queryValues)) + ";"

        # Insert into database
        database.query(query_string)


def prepare_table(database, table_name):
    for query in TABLE_PRE_QUERIES:
        database.query(query.format(table_name))


def postprocess_table(database, table_name):
    for query in TABLE_POST_QUERIES:
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
