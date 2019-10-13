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
    def __init__(self, table_name, filter_conditions_list, thread_count):
        self.table_name = table_name
        self.filter_conditions_list = filter_conditions_list
        self.thread_count = thread_count
        self.extracted_features = mp.Manager().list()

    def call_convert_script(self):
        # Build pipeline script call with parameters
        script_path = os.path.join(PIPELINE_DIR, CONVERT_SCRIPT_NAME)
        convert_process = os.popen(f"{script_path} \"{INPUT_FILE_PATH}\"")
        hashed_o5m_path = convert_process.read()
        if convert_process.close() is not None:
            print(f"[{self.table_name}] Error: Convert script execution failed.")
            exit(-1)

        return hashed_o5m_path

    def extract(self):
        # Dict for all extracted geometries
        geometries_dict = {}

        # Dict for all extracted labels
        labels_dict = {}

        # Convert input file to .o5m if needed
        hashed_o5m_path = self.call_convert_script()

        # Initialise Multiprocessing pool
        pool = mp.Pool(processes=self.thread_count)
        print(f"[{self.table_name}] There are {len(self.filter_conditions_list)} filter conditions. Extracting with {self.thread_count} threads.")

        count=0
        # Create threads to extract data with pipeline
        for filter_condition in self.filter_conditions_list:
            count += 1
            pool.apply_async(self.extract_with_pipeline, args=[f"{self.table_name}-{count}", hashed_o5m_path, filter_condition])

        # Wait for all threads to finish
        pool.close()
        pool.join()

        # Sanity check
        if len(self.extracted_features) < 1:
            print(f"[{self.table_name}] Error: Reading pipeline output failed.")
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

    def extract_with_pipeline(self, thread_name, hashed_o5m_path, filter_condition):
        print(f"[{thread_name}] Next filter condition: {filter_condition}")
        script_path = os.path.join(PIPELINE_DIR, PIPELINE_SCRIPT_NAME)
        pipeline_process = os.popen(f"{script_path} {thread_name} {hashed_o5m_path} {filter_condition}".replace("\n", ""))
        pipeline_output = pipeline_process.read()
        if pipeline_process.close() is not None:
            print(f"[{thread_name}] Error: Pipeline script execution failed.")
        loaded_features = json.loads(pipeline_output)["features"]
        print(f"[{thread_name}] Filter condition resulted in {len(loaded_features)} features")
        # Add features to list of all extracted features
        self.extracted_features.extend(loaded_features)
