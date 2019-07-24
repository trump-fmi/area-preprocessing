import copy
from Simplification import Simplification


class SimpleSimplification(Simplification):
    def __init__(self):
        pass

    def simplify(self, constraint_points, geometries, zoom):
        geometries_count = 0
        points_count = 0
        simplified_points_count = 0

        # Iterate over all geometries
        for geoIndex, geometry in geometries.items():

            # Geometry is a line string
            if geometry['type'] == 'LineString':
                coordinates = geometry['coordinates']

                # Count stats
                geometries_count += 1
                points_count += len(coordinates)

                # Apply simplification
                self.removeCoordinates(coordinates, zoom)
                geometries[geoIndex]['coordinates'] = coordinates

                # Count stats
                simplified_points_count += len(coordinates)

            # Geometry is a multi line string
            elif geometry['type'] == 'MultiLineString':
                line_strings = geometry['coordinates']

                for line_index, line_coordinates in enumerate(line_strings):
                    # Count stats
                    geometries_count += 1
                    points_count += len(line_coordinates)

                    # Apply simplification
                    self.removeCoordinates(line_coordinates, zoom)
                    line_strings[line_index] = line_coordinates

                    # Count stats
                    simplified_points_count += len(line_coordinates)

                line_strings[:] = [line for line in line_strings if len(line) > 1]

            # Geometry is a polygon
            elif geometry['type'] == 'Polygon':
                line_rings = geometry['coordinates']

                # Iterate over all contained line rings
                for ringIndex, ringCoordinates in enumerate(line_rings):
                    # Count stats
                    geometries_count += 1
                    points_count += len(ringCoordinates)

                    # Apply simplification
                    self.removeCoordinates(ringCoordinates, zoom)

                    line_rings[ringIndex] = ringCoordinates

                    # Count stats
                    simplified_points_count += len(ringCoordinates)

                line_rings[:] = [ring for ring in line_rings if len(ring) > 1]

            elif geometry['type'] == 'MultiPolygon':
                polygon_list = geometry['coordinates']

                for polygonIndex, line_rings in enumerate(polygon_list):
                    # Iterate over all contained line rings
                    for ringIndex, ringCoordinates in enumerate(line_rings):
                        # Count stats
                        geometries_count += 1
                        points_count += len(ringCoordinates)

                        # Apply simplification
                        self.removeCoordinates(ringCoordinates, zoom)
                        polygon_list[polygonIndex][ringIndex] = ringCoordinates

                        # Count stats
                        simplified_points_count += len(ringCoordinates)

                    polygon_list[polygonIndex][:] = [ring for ring in polygon_list[polygonIndex] if len(ring) > 1]
            else:
                print(f"Other geometry: {geometry['type']}")
                # raise Exception("Invalid geometry type")

        # Output stats
        print(f"---------- Zoom: {zoom} ----------")
        print(f"Geometries: {geometries_count}")
        print(f"Total points: {points_count}")
        print(f"Remaining points: {simplified_points_count}")
        print(f"Total points per geometry:  {points_count / geometries_count}")
        print(f"Remaining points per geometry:  {simplified_points_count / geometries_count}")
        print("----------------------------------")
        print()

        return geometries

    def removeCoordinates(self, coordinates, zoom):
        # Do nothing of zoom level is 19 or greater
        if int(zoom) >= 19:
            return

        n = zoom - 5
        if n < 1:
            n = 1

        # Iterate over all available coordinates
        for index, coordinate in enumerate(coordinates):
            # Remove every n-th coordinate
            if index % n == 0:
                coordinates.pop(index)
