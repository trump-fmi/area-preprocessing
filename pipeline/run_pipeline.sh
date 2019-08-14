#!/usr/bin/env bash

# ************ Usage *************
# 1st parameter: Input file to use (*.osm or *.pbf)
# 2nd parameter: Output file to produce (*.json)
# Following parameters: Osmfilter arguments
# ********************************

# ****** Name of temp files ******
TEMP_FILTERED="filtered.osm"
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
HASHED_NAME="$(sha256sum "$INPUT_FILE" | cut -d" " -f 1 | cut -c-10 ).o5m"

echo "Filename with content hash is $HASHED_NAME"

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

if [ ! -f /tmp/foo.txt ]; then
    # Convert input file
    echo "Converting input file to o5m format ($HASHED_NAME)..."
    osmconvert "${INPUT_FILE}" -o="${TEMP_O5M}"
else
    echo "Not converting input file because $HASHED_NAME already exists"
fi

# Filter OSM data
echo "Filtering for requested OSM data..."
osmfilter "${HASHED_NAME}" -o="${TEMP_FILTERED}" "$@"

# Convert result to GeoJSON
echo "Converting OSM data to GeoJSON..."
osmtogeojson -m "${TEMP_FILTERED}" > "${OUTPUT_FILE}"

# Remove all temp files
echo "Cleaning up..."
rm -f "${TEMP_FILTERED}"

echo "Successfully done."

exit 0
