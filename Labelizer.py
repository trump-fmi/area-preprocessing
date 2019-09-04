from subprocess import run, PIPE
from sys import exit
from ArcLabel import ArcLabel

BLACKBOX_PATH = "../area-labeling/standalone_lib/bin/bin/labeling"


class Labelizer:

    def __init__(self):
        self.output_dic = {}

    def labeling(self, geometries, labels):

        # TODO: Only a stub, replace if blackbox available
        if len(geometries) > 0:
            return {'7403': ArcLabel("testlabel", [8.234234, 48.23423], 3.14, 3.14 / 2, 0.06, 0.08)}

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
                polygon = geometry['coordinates'][0]

                outer_coordinates = polygon[0]
                if len(polygon) > 1:
                    inner_coordinates = polygon[1:]

                self.blackbox(geoIndex, outer_coordinates, inner_coordinates, labels[geoIndex])

            else:
                print(f"Other geometry: {geometry['type']}")
                # raise Exception("Invalid geometry type")

        return self.output_dic

    def blackbox(self, geoIndex, outer, inner, labelName):
        # Estimate Height/Length
        aspect = str(1 / len(labelName))

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

        # run black box
        label_process = run([BLACKBOX_PATH], stdout=PIPE, input=input_string,
                            encoding='ascii')

        if label_process.returncode is not 0:
            print("labeling command failed.")
            self.output_dic[geoIndex] = None

        label_output = label_process.stdout
        result = label_output.split()

        center = [float(result[0]), float(result[1])]
        self.output_dic[geoIndex] = ArcLabel(labelName, center, float(result[4]), float(result[5]), float(result[2]),
                                             float(result[3]))
