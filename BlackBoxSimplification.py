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

                line_strings[:] = [line for line in line_strings if len(line) > 1]

            # Geometry is a polygon
            elif geometry['type'] == 'Polygon':
                line_rings = geometry['coordinates']

                # Iterate over all contained line rings
                for ringIndex, ringCoordinates in enumerate(line_rings):
                    all_coordinates.append(ringCoordinates)

                line_rings[:] = [ring for ring in line_rings if len(ring) > 1]

            # Geometry is a multi polygon
            elif geometry['type'] == 'MultiPolygon':
                polygon_list = geometry['coordinates']

                for polygonIndex, line_rings in enumerate(polygon_list):
                    # Iterate over all contained line rings
                    for ringIndex, ringCoordinates in enumerate(line_rings):
                        all_coordinates.append(ringCoordinates)

                    polygon_list[polygonIndex][:] = [ring for ring in polygon_list[polygonIndex] if len(ring) > 1]
            else:
                print(f"Other geometry: {geometry['type']}")
                # raise Exception("Invalid geometry type")

        print("Running black box...")
        self.blackBox([], all_coordinates)

        return geometries

    def blackBox(self, constraints, coordinates):
        # create input string here
        input = ""
        for point in constraints:
            input += str(point)
        input += "\n"
        input += str(len(coordinates))
        input += "\n"
        for geometry in coordinates:
            for point in geometry:
                input += str(point)
            input += "\n"
        input = input.rstrip()

        # run black box
        xfree_process = run(["../topo_simplify/XFREE/build/xfree"], stdout=PIPE, input=input, encoding='ascii')

        if xfree_process.returncode is not 0:
            print("xfree command failed.")
            exit(1)

        xfree_output = xfree_process.stdout

        #print("xfree output:\n{}".format(xfree_output))

        topo_process = run(["../topo_simplify/CTR/build/topo_simplify"], stdout=PIPE, input=xfree_output, encoding='ascii')

        if topo_process.returncode is not 0:
            print("topo_simplify command failed.")
            exit(1)

        topo_output = topo_process.stdout

        return topo_output
