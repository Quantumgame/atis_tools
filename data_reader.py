import struct
import sys
from collections import namedtuple
import matplotlib.pyplot as plt
import numpy as np

EVENT_LENGTH = 8
PACKET_INFO_LENGTH = 12

# This should really be read from file, but it isn't now
RESX = 240
RESY = 180

Event = namedtuple('Event', ['type', 'subtype', 'y', 'x', 't'])
PacketInfo = namedtuple('PacketInfo', ['num_events', 'time_start', 'packet_type', 'packet_data'])
IMU6 = namedtuple('IMU6', ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'temp'])


class ATISReader(object):

	def __init__(self, filename = 'date_recording.bin'):
		
		self.event_list = []
		self.InitBinaryRead(filename)

	def InitBinaryRead(self, filename):
		# Open file and print header
		self.file = open(filename, mode = 'rb')
		header = self.file.readline()
		#print header
		if header == 'v2\n':
			#print "Version 2 found"
			header = self.file.readline()
		while header[0] == '#':
			print header
			header = self.file.readline()

	def ReadEvents(self, num_events = -1):
		data = 'tmp'
		while data != '':
			data = self.file.read(PACKET_INFO_LENGTH)
			# Read the packet info
			try:
				info = PacketInfo._make(struct.unpack('IIHH', data))
				#print "num_events = ", info.num_events, "; time_start = ", info.time_start
				#print hex(info.time_start)
				#raw_input()
				for i in range(info.num_events):
					data = self.file.read(EVENT_LENGTH)
					self.event_list.append(Event._make(struct.unpack('BBHHH', data)))
					# Hacky stuff to have absolute time
					self.event_list[-1] = self.event_list[-1]._replace(t = self.event_list[-1].t + (info.time_start << 16))
					#raw_input()
			except struct.error:
				print "EOF reached prematurely"
				break

	# Reads one image from the data. Code is repeated and ugly but whatever ain't nobody got time for that
	def ReadImage(self):
		image_found = False
		image_out = np.zeros((RESY,RESX), dtype = np.uint8)
		while image_found == False:
			data = self.file.read(PACKET_INFO_LENGTH)
			# Read the packet info
			try:
				info = PacketInfo._make(struct.unpack('IIHH', data))
				#print "num_events = ", info.num_events, "; time_start = ", info.time_start
				for i in range(info.num_events):
					data = self.file.read(EVENT_LENGTH)
					# Wait a bit (don't get the very first image captured by the sensor)
					if info.packet_type == 4 and info.time_start > 20:
						# It is a frame event
						e = Event._make(struct.unpack('BBHHH', data))
						image_out[e.y,e.x] = e.subtype
						# We don't really care about accurate time here
						image_found = True
			except struct.error:
				print "EOF reached prematurely"
				break
		return image_out

	def PlotHistograms(self):
		x_distr, y_distr = zip(*[(e.x, e.y) for e in self.event_list])
		plt.subplot(2,1,1)
		plt.hist(x_distr, bins = 240)
		plt.title("X events distribution")
		plt.xlabel("Pixel X coordinate")
		plt.ylabel("Number of TD events")

		plt.subplot(2,1,2)
		plt.hist(y_distr, bins = 180)
		plt.title("Y events distribution")
		plt.xlabel("Pixel Y coordinate")
		plt.ylabel("Number of TD events")
		plt.show()

	def FrequencyAnalysis(self):
		last_polarity = np.zeros((304,240)) - 1
		last_event_time = np.zeros((304,240)) - 1
		has_transitioned = np.zeros((304,240))
		frequencies_on = []
		frequencies_off = []
		frequencies_combined = []
		# The following is for opposite polarity checking
		for e in self.event_list:
			if last_polarity[e.x][e.y] != e.subtype:
				# I have an opposite polarity event, check if a 
				last_polarity[e.x][e.y] = e.subtype
				if last_event_time[e.x][e.y] != -1:
					# It has been initialized
					frequencies_combined.append(1000000.0 / (e.t - last_event_time[e.x][e.y]))
				last_event_time[e.x][e.y] = e.t
		# Check the same polarity, i.e. off -> on
		last_polarity = np.zeros((304,240)) - 1
		last_event_time = np.zeros((304,240)) - 1
		has_transitioned = np.zeros((304,240))
		for e in self.event_list:
			if e.subtype == 1:
				last_polarity[e.x][e.y] = 1;
				# I have an ON event, check if an on->off event in the same pixel happened already
				if has_transitioned[e.x][e.y] == True:
					has_transitioned[e.x][e.y] = False
					# Check that it is not the first event
					if last_event_time[e.x][e.y] != -1:
						# It has been initialized
						frequencies_on.append(1000000.0 / (e.t - last_event_time[e.x][e.y]))
				last_event_time[e.x][e.y] = e.t
			elif e.subtype == 0:
				if last_polarity[e.x][e.y] == 1:
					# A transition happened
					has_transitioned[e.x][e.y] = True
		last_polarity = np.zeros((304,240)) - 1
		last_event_time = np.zeros((304,240)) - 1
		has_transitioned = np.zeros((304,240))
		for e in self.event_list:
			if e.subtype == 0:
				last_polarity[e.x][e.y] = 0;
				# I have an OFF event, check if an off->on event in the same pixel happened already
				if has_transitioned[e.x][e.y] == True:
					has_transitioned[e.x][e.y] = False
					# Check that it is not the first event
					if last_event_time[e.x][e.y] != -1:
						# It has been initialized
						frequencies_off.append(1000000.0 / (e.t - last_event_time[e.x][e.y]))
				last_event_time[e.x][e.y] = e.t
			elif e.subtype == 1:
				if last_polarity[e.x][e.y] == 0:
					# A transition happened
					has_transitioned[e.x][e.y] = True

		self.FrequencyHistogram(frequencies_combined, frequencies_on, frequencies_off)

	def FrequencyHistogram(self, frequencies_combined, frequencies_on, frequencies_off):
		plt.subplot(3,1,1)
		plt.hist(frequencies_combined, bins = 1000, range = (0,3000))
		plt.title("Pixel frequencies, any transition")
		plt.xlabel("Frequency (Hz)")
		plt.ylabel("Number of occurences")

		plt.subplot(3,1,2)
		plt.hist(frequencies_on, bins = 1000, range = (0,3000))
		plt.title("Pixel frequencies, off->on transitions")
		plt.xlabel("Frequency (Hz)")
		plt.ylabel("Number of occurences")

		plt.subplot(3,1,3)
		plt.hist(frequencies_off, bins = 1000, range = (0,3000))
		plt.title("Pixel frequencies, on->off transitions")
		plt.xlabel("Frequency (Hz)")
		plt.ylabel("Number of occurences")
		plt.show()

	def PlotTimes(self):
		times = [e.t for e in self.event_list if e.type == 0]
		types = [e.type for e in self.event_list if e.type == 0]
		plt.plot(times)
		plt.show()
		unique_times = set(times)
		print "Number of times = ", len(times), "; Number of unique times = ", len(unique_times)

	def PrintIMU6Events(self):
		for e in self.event_list:
			if e.type == 11:
				# IMU Event
				# Calculate everything and output it
				if e.subtype == 0:
					print "\nAccel_x = ",
				elif e.subtype == 1:
					print "Accel_y = ",
				elif e.subtype == 2:
					print "Accel_z = ",
				elif e.subtype == 3:
					print "Gyro_x = ",
				elif e.subtype == 4:
					print "Gyro_y = ",
				elif e.subtype == 5:
					print "Gyro_z = ",
				elif e.subtype == 6:
					print "Temp = ",
				#print e
				# Creative byte operations to interpret two 16bit unsigned ints as a 32bit float
				msbs = struct.pack(">H", e.y)
				lsbs = struct.pack(">H", e.x)
				temp = struct.unpack(">f", (msbs+lsbs))[0]
				print temp

	# This is a function that only someone who did too much C++ and didn't remember that all class variables in Python are public
	# (like me) would write
	def getEvents(self):
		return self.event_list


def PlotDifferences(e_list1, e_list2):
	# Check which array is the shortest and calculate pairwise differences
	min_len = min([len(e_list1), len(e_list2)])
	diffs = []
	for i in range(min_len):
		diffs.append(e_list1[i].t - e_list2[i].t)
		#print e_list1[i].t, e_list2[i].t
		#print e_list1[i].t - e_list2[i].t
		#raw_input()
	t1 = [e.t for e in e_list1]
	t2 = [e.t for e in e_list2]	
	plt.subplot(3,1,1)
	plt.plot(t1)
	plt.title("Left camera timestamps")
	plt.xlabel("Event number")
	plt.ylabel("Timestamp")

	plt.subplot(3,1,2)
	plt.plot(t2)
	plt.title("Right camera timestamps")
	plt.xlabel("Event number")
	plt.ylabel("Timestamp")

	plt.subplot(3,1,3)
	plt.plot(diffs)
	plt.title("Difference timestamps")
	plt.xlabel("Event number")
	plt.ylabel("Timestamp")
	plt.show()


if __name__ == '__main__':
	if len(sys.argv) >= 2:
		r = ATISReader(sys.argv[1])
		r.ReadEvents()
	if len(sys.argv) == 3:
		r2 = ATISReader(sys.argv[2])
		r2.ReadEvents()
	#else:
	#	r = ATISReader()
	#	r.ReadEvents()
	#r.FrequencyAnalysis()
	#r.PlotHistograms()
	#r.PlotTimes()
	#r.PrintIMU6Events()
	el1 = r.getEvents()
	el2 = r2.getEvents()
	PlotDifferences(el1, el2)