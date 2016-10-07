import cv2
import numpy as np

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

	def __init__(self, use_nine=True):
		# Five points case
		if use_nine == True:
			# Nine points case
			self.platform = np.float32([ 
				[10,-10,0], [10,0,0], [10,10,0],
				[0,-10,0], [0,0,0], [0,10,0], 
				[-10,-10,0], [-10,0,0], [-10,10,0]])
			self.points = np.float32([
				[CENTER_X-DIM_X,CENTER_Y-DIM_Y], [CENTER_X,CENTER_Y-DIM_Y], [CENTER_X+DIM_X,CENTER_Y-DIM_Y], 
				[CENTER_X-DIM_X, CENTER_Y], [CENTER_X, CENTER_Y], [CENTER_X+DIM_X, CENTER_Y],
				[CENTER_X-DIM_X,CENTER_Y+DIM_Y], [CENTER_X,CENTER_Y+DIM_Y], [CENTER_X+DIM_X,CENTER_Y+DIM_Y]])
		else:
			self.platform = np.float32([[10,0,0], [0,10,0], [-10,0,0], [0,-10,0]])
			#self.points = np.float32([[CENTER_X,CENTER_Y-DIM_Y], [CENTER_X+DIM_X,CENTER_Y], [CENTER_X,CENTER_Y+DIM_Y], [CENTER_X-DIM_X,CENTER_Y]])
			#self.points = np.float32([[CENTER_X-DIM_X,CENTER_Y-DIM_Y], [CENTER_X+DIM_X,CENTER_Y-DIM_Y], [CENTER_X+DIM_X,CENTER_Y+DIM_Y], [CENTER_X-DIM_X,CENTER_Y+DIM_Y]])
			self.points = np.float32([[92,121], [176,31], [271,119], [196,226]])
			print self.points
		#self.CAMERA_MATRIX = np.float32([[533.74, 0, 150.03], [0, 533.88, 138.56], [0, 0, 1]])
		self.CAMERA_MATRIX = np.float32([[533.74, 0, CENTER_X], [0, 533.88, CENTER_Y], [0, 0, 1]])
		#print self.CAMERA_MATRIX

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


	def CalculatePNP(self):
		ret, rvec, tvec = cv2.solvePnP(self.platform, self.points, self.CAMERA_MATRIX, 0)
		rotM = cv2.Rodrigues(rvec)[0]
		cameraPosition = -np.matrix(rotM).T * np.matrix(tvec)
		print "Translation vector", tvec
		print "Rotation vector", rvec
		print "Camera position", cameraPosition



if __name__ == '__main__':
	#pf = PlatformFinder()
	#pf.CalculatePNP()
	#pf.ShowImages()
	#pf.ShowScene()
	pf2 = PlatformFinder(False)
	pf2.CalculatePNP()
	pf2.ShowImages()