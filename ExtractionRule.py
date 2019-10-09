import os
import json
import multiprocessing as mp

# ********** Config **********
PIPELINE_DIR = "pipeline"
PIPELINE_SCRIPT_NAME = "run_pipeline.sh"
CONVERT_SCRIPT_NAME = "convert.sh"
INPUT_FILE_PATH = "../../source_data.osm.pbf"
OUTPUT_FILE_NAME = "result.json"
GEOMETRIES_WHITELIST = ["LineString", "MultiLineString", "Polygon", "MultiPolygon"]
# ****************************


class ExtractionRule:
    def __init__(self, filter_conditions_list, thread_count):
        self.filter_conditions_list = filter_conditions_list
        self.thread_count = thread_count
        self.extracted_features = mp.Manager().list()

    def call_convert_script(self):
        # Build pipeline script call with parameters
        script_path = os.path.join(PIPELINE_DIR, CONVERT_SCRIPT_NAME)
        script_call = f"{script_path} \"{INPUT_FILE_PATH}\""

        # Execute script
        return_value = os.system(script_call)

        # Check script return value
        if return_value != 0:
            print("Error: Convert script execution failed.")
            exit(-1)

    def extract(self):
        # Dict for all extracted geometries
        geometries_dict = {}

        # Dict for all extracted labels
        labels_dict = {}

        # Convert input file to .o5m if needed
        self.call_convert_script()

        print(f"There are {len(self.filter_conditions_list)} filter conditions. Extracting with {self.thread_count} threads.")


        # Multiprocessing pool
        pool = mp.Pool(processes=self.thread_count)
        print(f"Preprocessing data on {self.thread_count} threads...")

        # Iterate over the list of filter conditions
        for filter_condition in self.filter_conditions_list:
            pool.apply_async(self.extract_with_pipeline, args=[filter_condition])

        # Wait for all threads to finish
        pool.close()
        pool.join()

        # Sanity check
        if len(self.extracted_features) < 1:
            print("Error: Reading pipeline output failed.")
            exit(-1)


        # Iterate over all extracted features
        for feature in self.extracted_features:

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

    def extract_with_pipeline(self, filter_condition):
        print(f"Next filter condition: {filter_condition}")
        script_path = os.path.join(PIPELINE_DIR, PIPELINE_SCRIPT_NAME)
        pipeline_process = os.popen(f"{script_path} {INPUT_FILE_PATH} {filter_condition}")
        pipeline_output = pipeline_process.read()
        if pipeline_process.close() is not None:
            print("Error: Pipeline script execution failed.")
        loaded_features = json.loads(pipeline_output)["features"]
        print(f"Filter condition resulted in {len(loaded_features)} features")
        # Add features to list of all extracted features
        self.extracted_features.extend(loaded_features)
