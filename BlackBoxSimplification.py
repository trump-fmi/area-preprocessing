import string

from Simplification import Simplification
from subprocess import run, PIPE
from sys import exit


class BlackBoxSimplification(Simplification):
    def __init__(self):
        pass

    def simplify(self, constraint_points, geometries, zoom):
        all_coordinates = []

        # Iterate over all geometries
        for geoIndex, geometry in geometries.items():

            # Geometry is a line string
            if geometry['type'] == 'LineString':
                all_coordinates.append(geometry['coordinates'])

            # Geometry is a multi line string
            elif geometry['type'] == 'MultiLineString':
                line_strings = geometry['coordinates']

                for line_index, line_coordinates in enumerate(line_strings):
                    all_coordinates.append(line_coordinates)

            # Geometry is a polygon
            elif geometry['type'] == 'Polygon':
                line_rings = geometry['coordinates']

                # Iterate over all contained line rings
                for ringIndex, ringCoordinates in enumerate(line_rings):
                    all_coordinates.append(ringCoordinates)

            # Geometry is a multi polygon
            elif geometry['type'] == 'MultiPolygon':
                polygon_list = geometry['coordinates']

                for polygonIndex, line_rings in enumerate(polygon_list):
                    # Iterate over all contained line rings
                    for ringIndex, ringCoordinates in enumerate(line_rings):
                        all_coordinates.append(ringCoordinates)

            else:
                print(f"Other geometry: {geometry['type']}")
                # raise Exception("Invalid geometry type")

        print("Running black box...")
        self.blackBox([], all_coordinates)

        return geometries

    def blackBox(self, constraint_points, coordinates):

        # Put input string together
        input_string = " ".join(map(lambda t: " ".join(map(str, t)), constraint_points))
        input_string += "\n"
        input_string += str(len(coordinates))
        input_string += "\n"
        input_string += "\n".join(map(lambda b: " ".join(map(lambda t: " ".join(map(str, t)), b)), coordinates))

        # run black box
        xfree_process = run(["../topo_simplify/XFREE/build/xfree"], stdout=PIPE, input=input_string, encoding='ascii')

        if xfree_process.returncode is not 0:
            print("xfree command failed.")
            exit(1)

        xfree_output = xfree_process.stdout

        topo_process = run(["../topo_simplify/CTR/build/topo_simplify"], stdout=PIPE, input=xfree_output,
                           encoding='ascii')

        if topo_process.returncode is not 0:
            print("topo_simplify command failed.")
            exit(1)

        topo_output = topo_process.stdout

        return topo_output
