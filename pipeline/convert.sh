#!/usr/bin/env bash

# ************ Usage *************
# 1st parameter: Input file to use (*.osm or *.pbf)
# ********************************

# Increase node RAM size (needed for osmtogeojson)
export NODE_OPTIONS=--max_old_space_size=16384

# Switch into pipeline directory
cd "${0%/*}"

# Uncomment for windows
# cd pipeline

# Store command line parameters
INPUT_FILE="$1"
HASHED_O5M_PATH="$(sha256sum "$INPUT_FILE" | cut -d" " -f 1 | cut -c-10 ).o5m"

echo "Source file is $INPUT_FILE. Filename with content hash is $HASHED_O5M_PATH" 1>&2

if [ ! -f "$HASHED_O5M_PATH" ]; then
    # Convert input file
    echo "Converting input file to o5m format ($HASHED_O5M_PATH)..." 1>&2
    osmconvert "${INPUT_FILE}" -o="${HASHED_O5M_PATH}"
else
    echo "Not converting input file because $HASHED_O5M_PATH already exists" 1>&2
fi

echo "${HASHED_O5M_PATH}"
