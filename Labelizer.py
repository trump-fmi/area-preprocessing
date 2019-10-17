from subprocess import run, PIPE
from sys import exit
from ArcLabel import ArcLabel

BLACKBOX_PATH = "../area_labeling/standalone_lib/build/bin/labeling"
LOG_FILE = open("labelizer_log.txt", "a+")

class Labelizer:

    def __init__(self):
        self.output_dic = {}

    def labeling(self, geometries, labels):

        for geoIndex, geometry in geometries.items():

            if not geoIndex in labels:
                continue

            outer_coordinates = []
            inner_coordinates = []

            # Geometry is a polygon
            if geometry['type'] == 'Polygon':

                # line_rings = geometry['coordinates']
                outer_coordinates = geometry['coordinates'][0]
                if len(geometry['coordinates']) > 1:
                    inner_coordinates = geometry['coordinates'][1:]

                self.blackbox(geoIndex, outer_coordinates, inner_coordinates, labels[geoIndex])

                # Geometry is a multi polygon
            elif geometry['type'] == 'MultiPolygon':

                current = None
                for polygon in geometry['coordinates']:
                    if current == None or len(current[0]) < len(polygon[0]):
                        current = polygon


                # polygon = geometry['coordinates'][0]

                outer_coordinates = current[0]
                if len(current) > 1:
                    inner_coordinates = current[1:]

                self.blackbox(geoIndex, outer_coordinates, inner_coordinates, labels[geoIndex])

            else:
                print(f"Other geometry: {geometry['type']}")
                # raise Exception("Invalid geometry type")

        return self.output_dic

    def blackbox(self, geoIndex, outer, inner, label_name):
        # Estimate Height/Length
        aspect = str(1 / (len(label_name) * 0.61))

        input_string = aspect + "\n"

        for coordinate in outer:
            input_string += str(coordinate[0]) + " " + str(coordinate[1]) + " "
        input_string += "\n"
        if len(inner) > 0:
            for hole in inner:
                input_string += "i\n"
                for coordinate in hole:
                    input_string += str(coordinate[0]) + " " + str(coordinate[1]) + " "
                input_string += "\n"

        input_string += "s\n"
                      
        # Logging
        LOG_FILE.write(f"Label {label_name}:")
        LOG_FILE.write(input_string)
        LOG_FILE.write("\n\n\n")

        # run black box
        label_process = run([BLACKBOX_PATH, "-s"], stdout=PIPE, input=input_string,
                            encoding='ascii')

        if label_process.returncode is not 0:
            print("labeling command failed.")
            self.output_dic[geoIndex] = None

        label_output = label_process.stdout

        result = label_output.split()

        if len(result) < 6:
            print("Fail :-(")
            return

        print("Subber")

        center = [float(result[0]), float(result[1])]
        self.output_dic[geoIndex] = ArcLabel(label_name, center, float(result[4]), float(result[5]), float(result[2]),
                                             float(result[3]))
