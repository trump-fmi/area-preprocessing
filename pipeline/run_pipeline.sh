#!/usr/bin/env bash

# ************ Usage *************
# 1st parameter: Input file to use (*.osm or *.pbf)
# Following parameters: Osmfilter arguments
# ********************************

# Increase node RAM size (needed for osmtogeojson)
export NODE_OPTIONS=--max_old_space_size=16384

# Switch into pipeline directory
cd "${0%/*}"

# Uncomment for windows
# cd pipeline

INPUT_FILE="$1"
HASHED_O5M_PATH="$(sha256sum "$INPUT_FILE" | cut -d" " -f 1 | cut -c-10 ).o5m"
TEMP_FILTERED="${HASHED_O5M_PATH}-filtered-$RANDOM.osm"

# Discard first command line parameter
shift 1

echo "Started extraction pipeline" 1>&2
echo "---------------------------------------------" 1>&2
echo "Input file: \"${INPUT_FILE}\"" 1>&2
echo "Hashed Filename: \"{HASHED_O5M_PATH}\"" 1>&2
echo "Filter parameters: \"$@\"" 1>&2

# Filter OSM data
echo "Filtering for requested OSM data..." 1>&2
osmfilter "${HASHED_O5M_PATH}" -o="${TEMP_FILTERED}" "$@"
# > "$TEMP_FILTERED"

# Convert result to GeoJSON
echo "Converting OSM data to GeoJSON and transforming to target projection..." 1>&2
osmtogeojson -m "${TEMP_FILTERED}" | reproject --use-epsg-io --from=EPSG:4326 --to=EPSG:3857

# Remove all temp files
echo "Cleaning up..." 1>&2
rm -f "${TEMP_FILTERED}" osmfilter_tempfile*

echo "Successfully done." 1>&2

exit 0
