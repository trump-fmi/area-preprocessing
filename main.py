#!/usr/bin/env python3
from ArcLabel import ArcLabel
from ExtractionRule import INPUT_FILE_PATH, ExtractionRule
from Labelizer import Labelizer
from NoSimplification import NoSimplification
from SimpleSimplification import SimpleSimplification
from BlackBoxSimplification import BlackBoxSimplification
from BlackboxSimplificationTest import BlackboxSimplificationTest
from database import DatabaseConnection
import os
import json
import time
from jsonschema import validate
import gc
import psutil
import math
import multiprocessing as mp

# File paths for area types JSON schema and document files
AREA_TYPES_DOCUMENT_FILE = "../area-types/area_types.json"
AREA_TYPES_SCHEMA_FILE = "../area-types/area_types_schema.json"

# Database settings
DATABASE_HOST = "trump-postgis"
DATABASE_NAME = "gis"
DATABASE_USER = "osm"
DATABASE_PASSWORD = "nieVooghee9fioSheicaizeiQueeyi2KaCh7boh2lei7xoo9CohtaeTe3mum"

# Maps geometry types to source tables in the database
SOURCE_TABLES = {
    "nodes": "planet_osm_point",
    "lines": "planet_osm_line",
    "polygons": "planet_osm_polygon"
}

# Coordinate projection of the generated output
OUTPUT_PROJECTION = "EPSG:3857"

# JSON key names of the area types definition
JSON_KEY_GROUPS_LIST = "groups"
JSON_KEY_GROUP_NAME = "name"
JSON_KEY_GROUP_TYPES = "types"
JSON_KEY_GROUP_TYPE_LABELS = "labels"
JSON_KEY_GROUP_TYPE_LABELS_ARCED = "arced"
JSON_KEY_GROUP_TYPE_LABELS_ZOOM_MIN = "zoom_min"
JSON_KEY_GROUP_TYPE_LABELS_ZOOM_MAX = "zoom_max"
JSON_KEY_GROUP_TYPE_TABLE_NAME = "table_name"
JSON_KEY_GROUP_TYPE_FILTERS = "filter_parameters"
JSON_KEY_GROUP_TYPE_SIMPLIFICATION = "simplification"
JSON_KEY_GROUP_TYPE_ZOOM_MIN = "zoom_min"
JSON_KEY_GROUP_TYPE_ZOOM_MAX = "zoom_max"

# Required queries for preparing a result table
TABLE_PRE_QUERIES = ["DROP TABLE IF EXISTS {0};",
                     """CREATE TABLE {0}
                     (
                         id INT NOT NULL,
                         geom GEOMETRY NOT NULL,
                         zoom INT DEFAULT 0,
                         geojson TEXT DEFAULT NULL,
                         label TEXT DEFAULT NULL,
                         label_center TEXT DEFAULT NULL,
                         start_angle FLOAT DEFAULT NULL,
                         end_angle FLOAT DEFAULT NULL,
                         inner_radius FLOAT DEFAULT NULL,
                         outer_radius FLOAT DEFAULT NULL,
                         CONSTRAINT {0}_unique_id UNIQUE (id, zoom)
                     );"""]

TABLE_INSERT_QUERY = "INSERT INTO {} (id,geom,zoom,geojson,label,label_center,start_angle,end_angle,inner_radius,outer_radius) VALUES %s;"
TABLE_INSERT_TEMPLATE = "(%s,ST_Transform(ST_Envelope(ST_GeomFromGeoJSON(%s)),4326),%s,%s,%s,%s,%s,%s,%s,%s)"

# Required queries for postprocessing a result table
TABLE_POST_QUERIES = ["CREATE INDEX {0}_geom_index ON {0} USING GIST(geom);",
                      "CREATE INDEX {0}_zoom_index ON {0} (zoom);"
                      "CLUSTER {0}_geom_index ON {0};"]

# Supported zoom range
ZOOM_RANGE = range(19, -1, -1)  # OSM default: range(0,19)

# Labelizer to use for ArcLabels
ARC_LABELIZER = Labelizer()

# Simplification algorithm to use
# SIMPLIFICATION = NoSimplification()
# SIMPLIFICATION = BlackboxSimplificationTest()

# Number of geometries to write within one database query
WRITE_BATCH_SIZE = 4000

# Database instance
database = None

LOG_FILE = open("main_geom_log_before.txt", "a+")
LOG_FILE_AFTER = open("main_geom_log_after.txt", "a+")


def extract_area_type(area_type):
    global database

    start_time = time.perf_counter()

    # Extract properties of interest from area type definition
    table_name = str(area_type[JSON_KEY_GROUP_TYPE_TABLE_NAME])
    filter_parameters = area_type[JSON_KEY_GROUP_TYPE_FILTERS]
    zoom_min = float(area_type[JSON_KEY_GROUP_TYPE_ZOOM_MIN])
    zoom_max = float(area_type[JSON_KEY_GROUP_TYPE_ZOOM_MAX])

    input_size = os.path.getsize(os.path.join("./pipeline", INPUT_FILE_PATH))
    needed_memory = input_size * 5
    available_memory = psutil.virtual_memory().available
    possible_threads = max(1, min(math.floor(available_memory / needed_memory), mp.cpu_count()))
    print(f"[{table_name}] Input size is {int(input_size / 1024 / 1024)}MiB,"
          f" needs {int(needed_memory / 1024 / 1024)}MiB memory (available: {int(available_memory / 1024 / 1024)}MiB)."
          f"-> Limiting to {int(available_memory / needed_memory)} threads")

    prepare_table(database, table_name)
    print(f"[{table_name}] Table prepared")

    # Create extraction rule and use it to extract geometries and labels
    print(f"[{table_name}] Extracting geometries...")
    extraction_rule = ExtractionRule(table_name, filter_parameters, possible_threads)
    geometries_dict, label_names_dict = extraction_rule.extract()
    print(f"[{table_name}] Extracted {len(geometries_dict)} geometries and {len(label_names_dict)} labels")

    # Create dictionary that maps geometry IDs to ArcLabels
    arc_labels_dict = {}

    # Check if arced labels are generally desired for this data
    if arced_labels_needed(area_type):
        print(f"[{table_name}] Calculating arced labels for geometries...")
        arc_labels_dict = ARC_LABELIZER.labeling(geometries_dict, label_names_dict)
        print(f"[{table_name}] Generated {len(label_names_dict.keys())} labels.")

    # Multiprocessing pool
    # TODO re-enable multithreading (currently crashes when multitple threads write to postgres)
    pool = mp.Pool(processes=1)
    print(f"[{table_name}] Preprocessing data on {possible_threads} threads...")

    # Iterate over all desired zoom levels
    for zoom in ZOOM_RANGE:
        # Check if zoom is within zoom range for this area type
        if (zoom < zoom_min) or (zoom >= zoom_max):
            continue

        pool.apply_async(process_for_zoom_level, args=(area_type, geometries_dict, arc_labels_dict, table_name, zoom))

    # Wait for all threads to finish
    pool.close()
    pool.join()

    # Reset simplification
    SIMPLIFICATION.clear()

    elapsed_time = time.perf_counter() - start_time
    print(f"[{table_name}] Processing finished. Took {elapsed_time:0.4} seconds")

    print(f"[{table_name}] Postprocessing table \"{table_name}\"...")
    postprocess_table(database, table_name)


def process_for_zoom_level(area_type, geometries_dict, arc_labels_dict, table_name, zoom_level):
    # Extract simplify property from area type
    simplify_geometries = bool(area_type[JSON_KEY_GROUP_TYPE_SIMPLIFICATION])

    # Logging
    geom_limit = 20
    for geoIndex, geometry in geometries_dict.items():
        geom_limit = geom_limit - 1
        if geom_limit == 0:
            break
        LOG_FILE.write(f"ID: {geoIndex}\n")
        LOG_FILE.write(geometry['type'])
        LOG_FILE.write("\n")
        LOG_FILE.write(str(geometry['coordinates']))
        LOG_FILE.write("\n\n\n")

    # Check if simplification is desired
    if simplify_geometries:
        print(f"[{table_name}-z{zoom_level}] Simplifying geometries for zoom level {zoom_level}...")
        simplified_geometries = SIMPLIFICATION.simplify(constraint_points=[], geometries=geometries_dict,
                                                        zoom=zoom_level)
    else:
        print(f"[{table_name}-z{zoom_level}] No simplification desired.")
        simplified_geometries = geometries_dict

    # Logging
    geom_limit = 20
    for geoIndex, geometry in simplified_geometries.items():
        geom_limit = geom_limit - 1
        if geom_limit == 0:
            break
        LOG_FILE_AFTER.write(f"ID: {geoIndex}\n")
        LOG_FILE_AFTER.write(geometry['type'])
        LOG_FILE_AFTER.write("\n")
        LOG_FILE_AFTER.write(str(geometry['coordinates']))
        LOG_FILE_AFTER.write("\n\n\n")

    # Write result to database
    print(f"[{table_name}-z{zoom_level}] Writing data to database...")
    write_data(table_name, area_type, simplified_geometries, arc_labels_dict, zoom_level)

    # Force garbage collection
    gc.collect()


# Checks if calculating arced labels is necessary for a given area type. If
# a zoom level is provided, it is checked specifically for this zoom level
def arced_labels_needed(area_type, zoom=None):
    # Check if label options provided
    if JSON_KEY_GROUP_TYPE_LABELS not in area_type: return False

    # Extract label options
    label_options = area_type[JSON_KEY_GROUP_TYPE_LABELS]
    arced = label_options[JSON_KEY_GROUP_TYPE_LABELS_ARCED]
    zoom_min = label_options[JSON_KEY_GROUP_TYPE_LABELS_ZOOM_MIN]
    zoom_max = label_options[JSON_KEY_GROUP_TYPE_LABELS_ZOOM_MAX]

    # Check if labels are required
    if zoom is None:
        return arced
    else:
        return arced and ((zoom >= zoom_min) and (zoom < zoom_max))


def write_data(table_name, area_type, geometries, arc_labels_dict, zoom):
    global database

    start_time = time.perf_counter()
    query_tuples = []
    try:
        for id, geometry in list(geometries.items()):
            # Extend geometry for SRID
            geometry['crs'] = {
                'type': 'name',
                'properties': {
                    'name': OUTPUT_PROJECTION
                }
            }
            # Stringify GeoJSON in a compact way
            geo_json = json.dumps(geometry, separators=(',', ':'))

            # Check if labels are required and there is one for the current geometry
            if arced_labels_needed(area_type, zoom) and (id in arc_labels_dict):
                # ArcLabel
                label_obj = arc_labels_dict[id]

                # Other label (if available)
                label = label_obj if isinstance(label_obj, ArcLabel) else ArcLabel(label_obj)
            else:
                # No label
                label = ArcLabel()

            query_tuple = (
                id, geo_json, zoom, geo_json, label.text, label.center, label.start_angle, label.end_angle,
                label.inner_radius,
                label.outer_radius)
            query_tuples.append(query_tuple)

        database.write_query(TABLE_INSERT_QUERY.format(table_name), template=TABLE_INSERT_TEMPLATE,
                             query_tuples=query_tuples, page_size=WRITE_BATCH_SIZE)
        elapsed_time = time.perf_counter() - start_time
        print(f'[{table_name}-z{zoom}] Wrote {len(query_tuples)} tuples to DB in {elapsed_time:0.4} seconds '
              f'with batch size {WRITE_BATCH_SIZE}')
    except Exception as e:
        print(f"write_data method failed with {e}")
        exit(1)

def prepare_table(database, table_name):
    for query in TABLE_PRE_QUERIES:
        database.write_query(query.format(table_name))


def postprocess_table(database, table_name):
    for query in TABLE_POST_QUERIES:
        database.write_query(query.format(table_name))


def read_area_types():
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
    return area_types[JSON_KEY_GROUPS_LIST]


def main():
    global database
    # Read area type definition from JSON file
    area_type_groups = read_area_types()

    # Connect to database
    print(f"Connecting to database \"{DATABASE_NAME}\" at \"{DATABASE_HOST}\" as user \"{DATABASE_USER}\"...")
    database = DatabaseConnection(host=DATABASE_HOST, database=DATABASE_NAME, user=DATABASE_USER,
                                  password=DATABASE_PASSWORD)
    print("Successfully connected")

    start_time = time.perf_counter()

    # Iterate over all area type groups
    for area_type_group in area_type_groups:
        # Get group name
        group_name = str(area_type_group[JSON_KEY_GROUP_NAME])

        # Get area types that belong to this group
        group_area_types = area_type_group[JSON_KEY_GROUP_TYPES]

        print(f"Next group: \"{group_name}\"")

        # Iterate over all area types of this group and invoke extraction
        for area_type in group_area_types:
            extract_area_type(area_type)

        print(f"Finished group \"{group_name}\"")

    elapsed_time = time.perf_counter() - start_time
    print(f"Simplification finished. Everything done. Took {elapsed_time:0.4} seconds")

    database.disconnect()


if __name__ == '__main__':
    main()
