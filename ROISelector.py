'''
This is actually taken from the internet, and readapted slightly to our purpose
Source: http://www.pyimagesearch.com/2015/03/09/capturing-mouse-click-events-with-python-and-opencv/
'''

# import the necessary packages
import argparse
import cv2
import numpy as np
import data_reader

# Davis values
RESX = 240
RESY = 180

class Selector(object):

	def __init__(self, image):
		self.image = image
		self.refPt = []
		self.cropping = False
		cv2.namedWindow("Scene")
		cv2.setMouseCallback("Scene", self.click_and_crop)
		self.MainLoop()

		self.ProcessROI()

	def MainLoop(self):
		# keep looping until the 'q' key is pressed
		while True:
			# display the image and wait for a keypress
			cv2.imshow("Scene", self.image)
			key = cv2.waitKey(1) & 0xFF
		 
			# if the 'c' key is pressed, break from the loop
			if key == ord("c"):
				break

	def click_and_crop(self, event, x, y, flags, param):
		# grab references to the global variables
	 
		# if the left mouse button was clicked, record the starting
		# (x, y) coordinates and indicate that cropping is being
		# performed
		if event == cv2.EVENT_LBUTTONDOWN:
			self.refPt.append((x, y))
			cropping = True
	 
		# check to see if the left mouse button was released
		elif event == cv2.EVENT_LBUTTONUP:
			# record the ending (x, y) coordinates and indicate that
			# the cropping operation is finished
			self.refPt.append((x, y))
			cropping = False
	 
			# draw a rectangle around the region of interest
			cv2.rectangle(self.image, self.refPt[-2], self.refPt[-1], 255, 2)
			cv2.imshow("Scene", self.image)

	

	def ProcessROI(self):
		# Get list of coordinates to ease processing
		ptx = [p[0] for p in self.refPt]
		pty = [p[1] for p in self.refPt]

		#print self.image.shape

		self.image_out = np.ones((self.image.shape[0], self.image.shape[1]), dtype=np.uint8)
		# Remove the selected areas from the binary image
		for i in range(0,len(self.refPt),2):
			#print ptx[i], ptx[i+1], pty[i], pty[i+1]
			# Check the ranges
			if ptx[i+1] > RESX:
				ptx[i+1] = RESX
			elif ptx[i+1] < 0:
				ptx[i+1] = 0
			if pty[i+1] > RESY:
				pty[i+1] = RESY
			elif pty[i+1] < 0:
				pty[i+1] = 0
			# IT BEGINS, four conditions to correctly index arrays (depending on how the user has dragged his square)
			if ptx[i+1] > ptx[i] and pty[i+1] > pty[i]:
				self.image_out[pty[i]:pty[i+1],ptx[i]:ptx[i+1]] = 0
			elif ptx[i+1] > ptx[i] and pty[i+1] < pty[i]:
				self.image_out[pty[i+1]:pty[i],ptx[i]:ptx[i+1]] = 0
			elif ptx[i+1] < ptx[i] and pty[i+1] > pty[i]:
				self.image_out[pty[i]:pty[i+1],ptx[i+1]:ptx[i]] = 0
			elif ptx[i+1] < ptx[i] and pty[i+1] < pty[i]:
				self.image_out[pty[i+1]:pty[i],ptx[i+1]:ptx[i]:] = 0
		# Show the filter mask
		cv2.imshow("Result", self.image_out * 255)
		cv2.waitKey(0)

	def WriteMask(self, filename = "roimask.bin"):
		self.image_out.tofile(filename)

if __name__ == '__main__':
	# Parse the input arguments of input and output files
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--input", required=False, help="Binary file containing scene image")
	ap.add_argument("-o", "--output", required=False, help="Output file containing the ROI mask")
	args = vars(ap.parse_args())
	if not args['input']:
		print "No input specified, will use the default file path data/davisframe.bin"
		dr = data_reader.ATISReader("data/davisframe.bin")
	else:
		dr = data_reader.ATISReader(args['input'])
	if not args['output']:
		print "No output specified, will use the default file path roiframe.bin"
		filename = "roimask.bin"
	else:
		filename = args['output']
	image = dr.ReadImage()
	# Stretch the grayscale to make it easier to visualize
	scaling_factor = 255 / np.amax(image)
	image = image * scaling_factor

	sel = Selector(image)
	# Save the mask to be imported into the epf
	sel.WriteMask(filename)