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
                    geometries[geoIndex]['coordinates'][ringIndex] = ringCoordinates

                    # Count stats
                    simplified_points_count += len(ringCoordinates)
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
                        geometries[geoIndex]['coordinates'][polygonIndex][ringIndex] = ringCoordinates

                        # Count stats
                        simplified_points_count += len(ringCoordinates)
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
