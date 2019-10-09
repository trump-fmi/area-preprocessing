# area-preprocessing
Processes the geometric area data that is stored in the database and simplifies it for different zoom levels

## Requirements

- `osmconvert`
- `osmfilter`
- `osmtogeojson` (npm)
- `reproject` (npm)
- `python3-psycopg2`
- `python3-psutil`
- `python3-jsonschema`
- [area-types](https://github.com/trump-fmi/area-types) cloned at the same level
- a `source_data.osm.pbf` file at the same level
