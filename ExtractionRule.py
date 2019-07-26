import os
import json

# ********** Config **********
PIPELINE_DIR = "pipeline"
PIPELINE_SCRIPT_NAME = "run_pipeline.sh"
INPUT_FILE_PATH = "../../source_data.osm.pbf"
OUTPUT_FILE_NAME = "result.json"
GEOMETRIES_WHITELIST = ["LineString", "MultiLineString", "Polygon", "MultiPolygon"]
TARGET_PROJECTION = 4326
# ****************************


class ExtractionRule:
    def __init__(self, filter_parameters):
        self.filter_parameters = filter_parameters

    def extract(self):
        # Dict for all extracted geometries
        geometries_dict = {}

        # Dict for all extracted names
        names_dict = {}

        # Build pipeline script call with parameters
        script_path = os.path.join(PIPELINE_DIR, PIPELINE_SCRIPT_NAME)
        script_call = script_path + f" \"{INPUT_FILE_PATH}\" \"{OUTPUT_FILE_NAME}\" {self.filter_parameters}"

        # Execute script
        return_value = os.system(script_call)

        if return_value != 0:
            print("Error: Pipeline script execution failed.")
            exit(-1)

        # Read in extracted GeoJSON data
        output_file_path = os.path.join(PIPELINE_DIR, OUTPUT_FILE_NAME)
        with open(output_file_path) as json_file:
            extracted_features = json.load(json_file)["features"]

        # Sanity check
        if extracted_features is None:
            print("Error: Reading pipeline output file failed.")
            exit(-1)

        # Iterate over all extracted features
        for feature in extracted_features:

            # Get feature id and extract number
            id = feature["id"]
            id = id.split("/", 1)[1]

            # Get feature geometry
            geometry = feature["geometry"]

            # Get geometry type
            geometry_type = geometry["type"]

            # Compare geometry type with whitelist
            if not geometry_type in GEOMETRIES_WHITELIST:
                continue

            # Get feature name if available
            name = None
            if "properties" in feature:
                if "name" in feature["properties"]:
                    name = feature["properties"]["name"]

            # If available, add sanitized name to name dict
            if name is not None:
                name = name.replace("'", "").replace("\"", "").replace("\n", "")
                names_dict[id] = name

            if id in geometries_dict:
                print("DUPLICATE!!!!!!!!!!!!!!!!!!!!!")

            # Add geometry to geometry dict
            geometries_dict[id] = geometry

        # Return resulting list of geometries
        return geometries_dict, names_dict
