from subprocess import run, PIPE
from sys import exit
from Simplification import Simplification
import json
import math
import numpy as np
import copy

BLACKBOX_PATH = "../topo_simplify/XFREE/build/make_x_free"
BLACKBOX_SIMPL_PATH = "../topo_simplify/CTR/build/topo_simplify"

MULTIPOLYGON = 1
POLYGON = 2
LINESTRING = 3
MULTILINESTRING = 4


class BlackboxSimplificationTest(Simplification):

	def __init__(self):
		self.newDict = {}

	def simplify(self, constraint_points,geometries,zoom):

		self.newDict = copy.deepcopy(geometries)
		mapping = []
		#CONSTRAINT POINTS
		string_input = ""
		for c_point in constraint_points:
			string_input += str(c_point[0])+" "+ str(c_point[1]) +" "
		string_input += "\n"
		
		geom_count = 50
		for geoIndex, geometry in geometries.items():
			geom_count = geom_count - 1
			if geom_count == 0:
				break

			if geometry['type'] == 'Polygon':
				#MAPPING FOR LATER RECREATION OF GEOMETRY(
				mapping.append([2, [(len(geometry['coordinates']))]])
				# INPUT FOR XFREE
				for boundary in geometry['coordinates']:
					for coordinate in boundary:
						string_input += str(coordinate[0]) + " " + str(coordinate[1]) + " "
					string_input += "\n"

			elif geometry['type'] == 'MultiPolygon':
				cur = []
				for polygon in geometry['coordinates']:
					cur.append(len(polygon))
					for boundary in polygon:
						for coordinate in boundary:
							string_input += str(coordinate[0]) + " " + str(coordinate[1]) + " "
						string_input += "\n"
				mapping.append([1,cur])
			
			elif geometry['type'] == 'LineString':
				mapping.append([3,[1]])
				for coordinate in geometry['coordinates']:
					string_input += str(coordinate[0]) + " " + str(coordinate[1]) + " "
				string_input += "\n"
		
			elif geometry['type'] == 'MultiLineString':
				mapping.append([4,[len(geometry['coordinates'])]])
				for linestring in geometry['coordinates']:
					for coordinate in linestring:
						string_input += str(coordinate[0]) + " " + str(coordinate[1]) + " "
					string_input += "\n"
	
	
		final_result = self.blackbox(string_input, zoom)

		#COMBINE BLACKBOX OUTPUT TO GEOMETRIES AGAIN
		index = 0
		coords = []
		for entry in mapping:

			type = entry[0]
			order = entry[1]

			if type == 3:
				coords.append(final_result[index])
				index += 1

			elif type == 2 or type == 4:

				sub_coords = []
				for i in range(index, index+order[0]):
					sub_coords.append(final_result[i])
				coords.append(sub_coords)
				index += order[0]

			elif type == 1:
				multipoly = []
				for amount in order:
					sub_coords = []
					for i in range(index, index+amount):
						sub_coords.append(final_result[i])
					index += amount
					multipoly.append(sub_coords)
				coords.append(multipoly)

		index = 0
		geom_count = 50
		for geoIndex, geometry in geometries.items():
			geom_count = geom_count - 1
			if geom_count == 0:
				break
			self.newDict[geoIndex]['coordinates'] = coords[index]
			index += 1
			

		return self.newDict

	def blackbox(self, xfree_input, zoom ):
		reassemble = []
		arr = []

	
		# XFREE BLACKBOX
		xfree_process = run(BLACKBOX_PATH, stdout=PIPE, input=xfree_input, encoding='ascii')
		xfree_output = xfree_process.stdout

		

		# XFREE OUTPUT
		constraints = xfree_output.split("\n")[0]
		result = xfree_output.split("\n")[1:-1]	
			
		# ARRAY FOR  LATER REASSEMBLY
			
		for entry in result[int(result[0])+2:]:
			line = list(map(int,entry.split(" ")[:-1]))
			new_arr = np.asarray(np.array_split(line,len(line)/2)).tolist()
			reassemble.append(new_arr)

	    # CREATE INPUT FOR CTR FROM XFREE OUTPUT ( OMIT MAPPING )
	
		ctr_input = constraints + "\n" + result[0] + "\n"
			
		for entry in result[1:int(result[0])+1]:
			ctr_input += entry + "\n"

	    # CTR BLACKBOX	
		epsilon = str((1/(zoom*100))* 100000)
		ctr_process = run([BLACKBOX_SIMPL_PATH, epsilon], stdout=PIPE, input=ctr_input, encoding='ascii')
		ctr_output = ctr_process.stdout

		ctr_result = ctr_output.split("\n")[1:-1]

		# OUTPUT LINES AS [[x1,y1],[x2,y2],...] #TODO: ONLY WORKS FOR SINGLE EPSILON ATM, EASY TO ADAPT
			
		for entry in ctr_result[2:]:		
			line = list(map(float,entry.split(" ")[:-1]))
			new_arr = np.asarray(np.array_split(line,len(line)/2)).tolist()
			arr.append(new_arr)
		
	
		final_result = self.recreate(arr,reassemble)
			
		return final_result

	def recreate(self, lines, mapping):
		geometries = []
		for entry in mapping:
			#first = True
			geometry = []
			for combination in entry:
				if combination[1] == 1:
					if len(geometry) >= 1 and geometry[-1] == lines[combination[0]][-1]:
						geometry.extend(lines[combination[0]][-2::-1])
					else: 
						geometry.extend(lines[combination[0]][::-1])						
				elif combination[1] == 0:
				    if len(geometry) >= 1 and geometry[-1] == lines[combination[0]][0]:
					    geometry.extend(lines[combination[0]][1:])
				    else: 
					    geometry.extend(lines[combination[0]])					    	

			geometries.append(geometry)	
		return geometries       
