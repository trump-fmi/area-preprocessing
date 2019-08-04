#!/usr/bin/env bash

# ************ Usage *************
# 1st parameter: Input file to use (*.osm or *.pbf)
# 2nd parameter: Output file to produce (*.json)
# Following parameters: Osmfilter arguments
# ********************************

# ****** Name of temp files ******
temp_o5m="converted_data.o5m"
temp_filtered="filtered.osm"
# ********************************

# Increase node RAM size
export NODE_OPTIONS=--max_old_space_size=16384

# Switch into pipeline directory
cd "${0%/*}"

# Uncomment for windows
# cd pipeline

# Store command line parameters
input_file="$1"
output_file="$2"

# Discard first two command line parameters
shift 2

echo "Started extraction pipeline"
echo "---------------------------------------------"
echo "Input file: \"${input_file}\""
echo "Output file: \"${output_file}\""
echo "Filter parameters: \"$@\""

# Install/Update osmtogeojson
echo "Updating components..."
npm install -g osmtogeojson

# Remove old stuff
echo "Removing old JSON files..."
rm -f *.json

# Convert input file
echo "Converting input file to o5m format..."
./osmconvert "${input_file}" -o="${temp_o5m}"

# Filter OSM data
echo "Filtering for requested OSM data..."
./osmfilter "${temp_o5m}" -o="${temp_filtered}" "$@"

# Convert result to GeoJSON
echo "Converting OSM data to GeoJSON..."
osmtogeojson -m "${temp_filtered}" > "${output_file}"

# Remove all temp files
echo "Cleaning up..."
rm -f temp_o5m = "${temp_o5m}"
rm -f "${temp_filtered}"

echo "Successfully done."

exit 0