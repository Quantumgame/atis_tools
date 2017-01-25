import cv2
import numpy as np
import csv
import matplotlib.pyplot as plt
import sys

RESX = 304
RESY = 240

SCENE_SIZEX = 40
SCENE_SIZEY = 30
SCENE_CENTERX = 20
SCENE_CENTERY = 15

DIM_X = 50
DIM_Y = 50
CENTER_X = 152
CENTER_Y = 120

class PlatformFinder(object):

	def __init__(self):
		# Five points case
		self.platform = np.float32([[0,0,0], [0,10,0], [10,0,0], [0,-10,0], [-10,0,0]])
		#self.points = np.float32([[92,121], [176,31], [271,119], [196,226]])
		self.points = []
		self.camera_positions = []
		self.times = []
		#self.CAMERA_MATRIX = np.float32([[533.74, 0, 150.03], [0, 533.88, 138.56], [0, 0, 1]])
		self.CAMERA_MATRIX = np.float32([[533.74, 0, CENTER_X], [0, 533.88, CENTER_Y], [0, 0, 1]])

	def ShowImages(self):
		points_image = np.zeros((RESY,RESX))
		for coords in self.points:
			points_image[coords[1], coords[0]] = 255
		cv2.imshow('Points seen by camera', points_image)
		cv2.waitKey(0)
		cv2.destroyAllWindows()

	def ShowScene(self):
		points_image = np.zeros((SCENE_SIZEY,SCENE_SIZEX))
		for coords in self.platform:
			points_image[SCENE_CENTERY + coords[0], SCENE_CENTERX + coords[1]] = 255
		cv2.imshow('Points in scene', points_image)
		cv2.waitKey(0)
		cv2.destroyAllWindows()


	def CalculatePNP(self, image_points):
		ret, rvec, tvec = cv2.solvePnP(self.platform, image_points, self.CAMERA_MATRIX, 0)
		#ret, mask = cv2.findHomography(self.platform, image_points, )
		rotM = cv2.Rodrigues(rvec)[0]
		cameraPosition = -np.matrix(rotM).T * np.matrix(tvec)
		self.camera_positions.append(cameraPosition)
		#print "Translation vector", tvec
		#print "Rotation vector", rvec
		#print "Camera position", cameraPosition
		#self.camera_positions.append(cameraPosition)

	def LoadMarkerCsv(self, filepath = 'data/marker_data.csv'):
		with open(filepath, 'rb') as csvfile:
			reader = csv.reader(csvfile, delimiter=',')
			# Skip the header
			reader.next()
			count = 0
			for row in reader:
				#self.points.append(row)
				self.times.append(float(row[0]))
				count = count + 1
				points = np.asarray(row[1:], dtype = float).reshape((5,2))
				self.CalculatePNP(points)
		self.ProcessTimes()
		

	def ProcessTimes(self):
		self.times = np.array(self.times)
		self.times = self.times - self.times[0]
		self.camera_positions = np.asarray(self.camera_positions, dtype = float)
		#self.times = self.times / 1000000.0

	def FilterDataMA(self, data, ma_size = 30):
		return np.convolve(data, np.ones((ma_size))/ma_size, mode = 'same')

	def FilterDataAR(self, data, ar_weight = 0.25):
		data[0] = 0
		for i in range(1,len(data)):
			data[i] = ar_weight * data[i] + (1 - ar_weight) * data[i-1]
		return data

	def PlotCameraPositions(self):
		x = [float(r[0]) for r in self.camera_positions]
		y = [float(r[1]) for r in self.camera_positions]
		z = [float(r[2]) for r in self.camera_positions]
		t = [r for r in self.times]
		plt.subplot(3, 1, 1)
		plt.plot(t,x,'b')
		plt.hold(True)
		x = self.FilterDataMA(x)
		plt.plot(t,x,'r')
		x = self.FilterDataAR(x)
		plt.plot(t,x,'g')
		plt.xlabel("t (s)")
		plt.ylabel("x (cm)")

		plt.subplot(3, 1, 2)
		plt.plot(t,y,'b')
		plt.hold(True)
		y = self.FilterDataMA(y)
		plt.plot(t,y,'r')
		y = self.FilterDataAR(y)
		plt.plot(t,y,'g')
		plt.xlabel("t (s)")
		plt.ylabel("y (cm)")

		plt.subplot(3, 1, 3)
		plt.plot(t,z,'b')
		plt.hold(True)
		z = self.FilterDataMA(z)
		plt.plot(t,z,'r')
		z = self.FilterDataAR(z)
		plt.plot(t,z,'g')
		plt.xlabel("t (s)")
		plt.ylabel("z (cm)")
		plt.show()

if __name__ == '__main__':
	pf = PlatformFinder()
	if len(sys.argv) == 2:
		pf.LoadMarkerCsv(sys.argv[1])
	else:
		pf.LoadMarkerCsv()
	pf.PlotCameraPositions()
	#pf2.CalculatePNP()
	#pf2.ShowImages()