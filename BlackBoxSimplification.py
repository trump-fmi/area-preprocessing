import string

from Simplification import Simplification
from subprocess import run, PIPE
from sys import exit


class BlackBoxSimplification(Simplification):
    def __init__(self):
        pass

    def simplify(self, constraint_points, geometries, zoom):
        all_coordinates = []
        all_geometries = []

        # Iterate over all geometries
        for geoIndex, geometry in geometries.items():

            # Geometry is a line string
            if geometry['type'] == 'LineString':
                all_coordinates.append(geometry['coordinates'])
                all_geometries.append(geometry)

            # Geometry is a multi line string
            elif geometry['type'] == 'MultiLineString':
                line_strings = geometry['coordinates']

                for line_index, line_coordinates in enumerate(line_strings):
                    all_coordinates.append(line_coordinates)
                    all_geometries.append(geometry)

            # Geometry is a polygon
            elif geometry['type'] == 'Polygon':
                line_rings = geometry['coordinates']

                # Iterate over all contained line rings
                for ringIndex, ringCoordinates in enumerate(line_rings):
                    all_coordinates.append(ringCoordinates)
                    all_geometries.append(geometry)

            # Geometry is a multi polygon
            elif geometry['type'] == 'MultiPolygon':
                polygon_list = geometry['coordinates']

                for polygonIndex, line_rings in enumerate(polygon_list):
                    # Iterate over all contained line rings
                    for ringIndex, ringCoordinates in enumerate(line_rings):
                        all_coordinates.append(ringCoordinates)
                        all_geometries.append(geometry)

            else:
                print(f"Other geometry: {geometry['type']}")
                # raise Exception("Invalid geometry type")

        print("Running black box...")
        #simplified_geometries = self.blackBox([[9.1067832, 48.7448467], [9.2190092, 48.6600964], [8.8484828, 48.6103653]], all_coordinates)
        blackbox_out, xfree_out = self.blackBox([], all_coordinates)      

        ###
        # put simplified border parts back to borders
        ###
        border_parts = blackbox_out.split('\n')
        del border_parts[0] # remove constraint points
        del border_parts[0] # remove line count
        simplified_geometries = []

        # "jump" to mappings and handle them
        number_of_mappings = xfree_out[1] + 1
        for current_mapping in range(number_of_mappings, xfree_out[number_of_mappings] + 1):
            simplified_geometries.append(resolveMapping(current_mapping, border_parts))


        ###
        # match borders to their geometries
        ###
        if len(simplified_geometries) != len(all_geometries):
            print("simplified border count does not match original border count")
            exit()
        
        # loop through geometries and put simplified borders there

        return geometries


    def resolveMapping(mapping, border_parts):
        retVal = ""
        values = mapping.split(' ')
        count = 0
        while count < len(values):
            tmp = border_parts[mapping[count]]
            count += 1
            if mapping[count] == 0:
                retVal = addPart(retVal, tmp, false)
            elif mapping[count] == 1:
                retVal = addPart(retVal, tmp, true)
            count += 1
        return retVal


    # add new part without having double points
    def addPart(existing, new, reverse):
        existing = existing.split(' ')
        new = new.split(' ')
        
        if reverse:
            tmp = []
            count = len(new) - 2 # point to second last element in new
            while count > 0:
                tmp.append(new[count])
                count += 1
                tmp.append(new[count])
                count -= 3
            new = tmp
        
        if existing[len(existing)-2] != new[0] or existing[len(existing-1)] != new[1]:
            print("endpoint of existing part different from startpoint of new part")
            exit()
        
        # drop first point of new segment to avoid double points
        del new[0]
        del new[0]
        existing.append(new)

        return ' '.join(existing)

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

        # chose 0.3 as epsilon value, might need adjustment
        topo_process = run(["../topo_simplify/CTR/build/topo_simplify", "0.3"], stdout=PIPE, input=xfree_output,
                           encoding='ascii')

        if topo_process.returncode is not 0:
            print("topo_simplify command failed.")
            exit(1)

        topo_output = topo_process.stdout


        return topo_output, xfree_output.split('\n')
