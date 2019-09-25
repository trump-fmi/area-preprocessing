#!/usr/bin/env bash

# ************ Usage *************
# 1st parameter: Input file to use (*.osm or *.pbf)
# 2nd parameter: Output file to produce (*.json)
# Following parameters: Osmfilter arguments
# ********************************

# ****** Name of temp files ******
TEMP_FILTERED="filtered.osm"
TEMP_CONVERTED="converted.json"
# ********************************

# Increase node RAM size
export NODE_OPTIONS=--max_old_space_size=16384

# Switch into pipeline directory
cd "${0%/*}"

# Uncomment for windows
# cd pipeline

# Store command line parameters
INPUT_FILE="$1"
OUTPUT_FILE="$2"
HASHED_O5M_PATH="$(sha256sum "$INPUT_FILE" | cut -d" " -f 1 | cut -c-10 ).o5m"

echo "Filename with content hash is $HASHED_O5M_PATH"

# Discard first two command line parameters
shift 2

echo "Started extraction pipeline"
echo "---------------------------------------------"
echo "Input file: \"${INPUT_FILE}\""
echo "Output file: \"${OUTPUT_FILE}\""
echo "Filter parameters: \"$@\""

# Remove old stuff
echo "Removing old JSON files..."
rm -f *.json

if [ ! -f "$HASHED_O5M_PATH" ]; then
    # Convert input file
    echo "Converting input file to o5m format ($HASHED_O5M_PATH)..."
    osmconvert "${INPUT_FILE}" -o="${HASHED_O5M_PATH}"
else
    echo "Not converting input file because $HASHED_O5M_PATH already exists"
fi

# Filter OSM data
echo "Filtering for requested OSM data..."
osmfilter "${HASHED_O5M_PATH}" -o="${TEMP_FILTERED}" "$@"

# Convert result to GeoJSON
echo "Converting OSM data to GeoJSON..."
osmtogeojson -m "${TEMP_FILTERED}" > "${TEMP_CONVERTED}"

# Convert result to GeoJSON
echo "Transforming coordinates to target projection..."
cat "${TEMP_CONVERTED}" | reproject --use-epsg-io --from=EPSG:4326 --to=EPSG:3857 > "${OUTPUT_FILE}"

# Remove all temp files
echo "Cleaning up..."
rm -f "${TEMP_FILTERED}"
rm -f "${TEMP_CONVERTED}"

echo "Successfully done."

exit 0
