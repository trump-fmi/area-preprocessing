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
    def __init__(self, filter_conditions_list):
        self.filter_conditions_list = filter_conditions_list

    def extract(self):
        # Dict for all extracted geometries
        geometries_dict = {}

        # Dict for all extracted labels
        labels_dict = {}

        # Stores all features that were extracted by the various filter conditions
        extracted_features = []

        print(f"There are {len(self.filter_conditions_list)} filter conditions")

        # Iterate over the list of filter conditions
        for filter_condition in self.filter_conditions_list:

            print(f"Next filter condition: {filter_condition}")

            # Build pipeline script call with parameters
            script_path = os.path.join(PIPELINE_DIR, PIPELINE_SCRIPT_NAME)
            script_call = script_path + f" \"{INPUT_FILE_PATH}\" \"{OUTPUT_FILE_NAME}\" {filter_condition}"

            # Execute script
            return_value = os.system(script_call)

            # Check script return value
            if return_value != 0:
                print("Error: Pipeline script execution failed.")
                exit(-1)

            # Read in extracted GeoJSON data
            output_file_path = os.path.join(PIPELINE_DIR, OUTPUT_FILE_NAME)
            with open(output_file_path) as json_file:
                # Retrieve features
                loaded_features = json.load(json_file)["features"]
                print(f"Filter condition resulted in {len(loaded_features)} features")

                # Add features to list of all extracted features
                extracted_features.extend(loaded_features)

            # Sanity check
            if len(extracted_features) < 1:
                print("Error: Reading pipeline output failed.")
                exit(-1)

        # Iterate over all extracted features
        for feature in extracted_features:

            # Get feature id and extract number
            id = feature["id"]
            id = id.split("/", 1)[1]

            # Check if geometry with this id has been already extracted
            if id in geometries_dict:
                continue

            # Get feature geometry
            geometry = feature["geometry"]

            # Get geometry type
            geometry_type = geometry["type"]

            # Compare geometry type with whitelist
            if not geometry_type in GEOMETRIES_WHITELIST:
                continue

            # Get name tag of feature as label if available
            label = None
            if "properties" in feature:
                if "name" in feature["properties"]:
                    label = feature["properties"]["name"]

            # If available, add sanitized label to label dict
            if label is not None:
                label = label.replace("'", "").replace("\"", "").replace("\n", "")
                labels_dict[id] = label

            # Add geometry to geometry dict
            geometries_dict[id] = geometry

        # Return resulting list of geometries
        return geometries_dict, labels_dict
