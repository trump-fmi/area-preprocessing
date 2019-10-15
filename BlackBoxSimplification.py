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
        count = 0
        # Iterate over all geometries
        for geoIndex, geometry in geometries.items():

            # Geometry is a line string
            if geometry['type'] == 'LineString':
                count +=1
                #print(geoIndex)
                #print(geometry)
                #if count ==2:
                #    exit()
                all_coordinates.append(geometry['coordinates'])
                all_geometries.append((geometry, geoIndex, None, None))

                #print(all_geometries)
                #exit()

            # Geometry is a multi line string
            elif geometry['type'] == 'MultiLineString':
                line_strings = geometry['coordinates']

                for line_index, line_coordinates in enumerate(line_strings):
                    all_coordinates.append(line_coordinates)
                    all_geometries.append((geometry, geoIndex, line_index, None))

            # geometry is a polygon
            elif geometry['type'] == 'Polygon':
                line_rings = geometry['coordinates']

                # Iterate over all contained line rings
                for ringIndex, ringCoordinates in enumerate(line_rings):
                    all_coordinates.append(ringCoordinates)
                    all_geometries.append((geometry, geoIndex, ringIndex, None))

            # Geometry is a multi polygon
            elif geometry['type'] == 'MultiPolygon':
                polygon_list = geometry['coordinates']

                for polygonIndex, line_rings in enumerate(polygon_list):
                    # Iterate over all contained line rings
                    for ringIndex, ringCoordinates in enumerate(line_rings):
                        all_coordinates.append(ringCoordinates)
                        all_geometries.append((geometry, geoIndex, polygonIndex, ringIndex))

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
        # output of xfree:
        #    [0] constraint points
        #    [1] number of borders = X
        #  [...] X times one border per line
        #  [X+2] number of mappings = Y
        #  [...] Y times one mapping per line
        
        mappings_start = int(int(xfree_out[1]) + 3)

        for current_mapping in range(mappings_start, len(xfree_out) - 1):
            print(xfree_out[current_mapping])
            simplified_geometries.append(self.resolveMapping(xfree_out[current_mapping], border_parts))


        ###
        # match borders to their geometries
        ###
        if len(simplified_geometries) != len(all_geometries):
            print("simplified border count does not match original border count")
            #exit()
        
        # loop through geometries and put simplified borders there
        current_coordinates = None
        have_polygon = False
        previous_geometry = None
        previous_geoIndex = None
        previous_2ndIndex = None
        previous_3rdIndex = None
        
        for geometry_data, coordinates in zip(all_geometries, all_coordinates):
            current_geometry = geometry_data[0]
            current_geoIndex = geometry_data[1]
            current_2ndIndex = geometry_data[2]
            current_3rdIndex = geometry_data[3]
            
            # got new polygon, save what we got
            if current_2ndIndex != previous_2ndIndex and have_polygon == True:
                previous_geometry['coordinates'][previous_2ndIndex] = current_coordinates
                have_polygon = False

            # got new geometry, save what we got
            if current_geoIndex != previous_geoIndex and previous_geometry != None and previous_geometry['type'] != 'MultiPolygon':
                previous_geometry['coordinates'] = current_coordinates
                previous_geometry = None

            if geometry['type'] == 'LineString':
                current_geometry['coordinates'] = coordinates
                #print(geometry)
                #exit()
            
            elif geometry['type'] == 'MultiLineString' or geometry['type'] == 'Polygon':
                if previous_geometry == None:
                    previous_geometry = current_geometry
                    previous_geoIndex = current_geoIndex
                    current_coordinates = coordinates                  

                current_coordinates += "\n" + coordinates

                #print(geometry)
                #exit()
            
            elif geometry['type'] == 'MultiPolygon':
                if have_polygon == False:
                    have_polygon = True
                    previous_geometry = current_geometry
                    previous_geoIndex = current_geoIndex
                    previous_2ndIndex = current_2ndIndex
                    current_coordinates = coordinates                  

                current_coordinates += "\n" + coordinates

                

        return geometries


    def resolveMapping(self, mapping, border_parts):
        retVal = ""
#        print(mapping)
        values = mapping.split(' ')
        count = 0
#        print("len val: " + str(len(values)))
#        print(values)
        while count < len(values) - 1:
#            print("current count: " + mapping[count])
            tmp = border_parts[int(mapping[count])]
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
        #input_string += "\n"
        #input_string += str(len(coordinates))
        input_string += "\n"
        input_string += "\n".join(map(lambda b: " ".join(map(lambda t: " ".join(map(str, t)), b)), coordinates))

        #print("\nDEBUG: READING FROM tmp2.txt\n")
        #with open('tmp2.txt', 'r') as data_file:
        #    input_string = data_file.read()

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
