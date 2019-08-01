from Simplification import Simplification
from subprocess import run, PIPE
from sys import exit


class BlackBoxSimplification(Simplification):
    def __init__(self):
        pass

    def simplify(self, geometries, zoom):
        geometries_count = 0
        points_count = 0
        simplified_points_count = 0
        all_coordinates = []

        # Iterate over all geometries
        for geoIndex, geometry in geometries.items():

            # Geometry is a line string
            if geometry['type'] == 'LineString':
                #if all_coordinates == None:
                all_coordinates.append(geometry['coordinates'])
                #else:
                #    all_coordinates += geometry['coordinates']

                # Count stats
                geometries_count += 1
                #points_count += len(coordinates)

                # Apply simplification
                #self.removeCoordinates(coordinates, zoom)
                #geometries[geoIndex]['coordinates'] = coordinates

                # Count stats
                #simplified_points_count += len(coordinates)

            # Geometry is a multi line string
            elif geometry['type'] == 'MultiLineString':
                line_strings = geometry['coordinates']

                for line_index, line_coordinates in enumerate(line_strings):

                    #if all_coordinates == None:
                    all_coordinates.append(line_coordinates)
                    #print(all_coordinates)
                    #else:
                    #    all_coordinates += line_coordinates

                  # Count stats
                    geometries_count += 1
                    points_count += len(line_coordinates)

                    # Apply simplification
                    #self.removeCoordinates(line_coordinates, zoom)
                    #line_strings[line_index] = line_coordinates

                    # Count stats
                    simplified_points_count += len(line_coordinates)

                line_strings[:] = [line for line in line_strings if len(line) > 1]

            # Geometry is a polygon
            elif geometry['type'] == 'Polygon':
                line_rings = geometry['coordinates']

                # Iterate over all contained line rings
                for ringIndex, ringCoordinates in enumerate(line_rings):
                    #if all_coordinates == None:
                    all_coordinates.append(ringCoordinates)
                    #else:
                    #    all_coordinates += ringCoordinates

                    # Count stats
                    geometries_count += 1
                    points_count += len(ringCoordinates)


                    # Apply simplification
                    #self.removeCoordinates(ringCoordinates, zoom)
                    #line_rings[ringIndex] = ringCoordinates

                    # Count stats
                    simplified_points_count += len(ringCoordinates)

                line_rings[:] = [ring for ring in line_rings if len(ring) > 1]

            elif geometry['type'] == 'MultiPolygon':
                polygon_list = geometry['coordinates']

                for polygonIndex, line_rings in enumerate(polygon_list):
                    # Iterate over all contained line rings
                    for ringIndex, ringCoordinates in enumerate(line_rings):

                        #if all_coordinates == None:
                        all_coordinates.append(ringCoordinates)
                        #else:
                        #    all_coordinates += ringCoordinates

                        # Count stats
                        geometries_count += 1
                        points_count += len(ringCoordinates)


                        # Apply simplification
                        #self.removeCoordinates(ringCoordinates, zoom)
                        #polygon_list[polygonIndex][ringIndex] = ringCoordinates

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

        print("getting constraints...")
        self.getConstraints(zoom)

        print("running black box...")
        self.blackBox([], geometries_count, all_coordinates)

        return geometries



    def blackBox(self, constraints, geometries_count, coordinates):
        # create input string here
        input = ""
        for point in constraints:
            input += str(point)
        input += "\n"
        input += str(geometries_count)
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



    def getConstraints(self, zoom):
        # figure out how to do this
        print("--- constraints not implemented yet---")
