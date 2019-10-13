#!/usr/bin/env bash

# ************ Usage *************
# 1st parameter: Instance name for logging
# 2nd parameter: Converted input file to use (*.o5m)
# Following parameters: Osmfilter arguments
# ********************************

# Increase node RAM size (needed for osmtogeojson)
export NODE_OPTIONS=--max_old_space_size=16384

# Switch into pipeline directory
cd "${0%/*}"

# Uncomment for windows
# cd pipeline
INSTANCE="$1"
INPUT_FILE="$2"
TEMP_FILTERED="${INPUT_FILE}-filtered-$RANDOM.osm"
OSMFILTER_TEMPFILE="${INPUT_FILE}-osmfilter-temp-$RANDOM.osm"

# Discard first two command line parameters
shift 2

echo "[$INSTANCE] Started extraction pipeline" 1>&2
echo "[$INSTANCE] Input file: \"${INPUT_FILE}\"" 1>&2

# Filter OSM data
echo "[$INSTANCE] Filtering for requested OSM data with parameters: \"$@\"" 1>&2
osmfilter "${INPUT_FILE}" -o="${TEMP_FILTERED}" -t="${OSMFILTER_TEMPFILE}" "$@"

# Convert result to GeoJSON
echo "[$INSTANCE] Converting OSM data to GeoJSON and transforming to target projection..." 1>&2
osmtogeojson -m "${TEMP_FILTERED}" | reproject --use-epsg-io --from=EPSG:4326 --to=EPSG:3857

# Remove all temp files
rm -f "${TEMP_FILTERED}" "${OSMFILTER_TEMPFILE}"

echo "[$INSTANCE] Successfully done." 1>&2
