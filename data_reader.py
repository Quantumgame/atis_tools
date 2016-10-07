import struct
import sys
from collections import namedtuple
import matplotlib.pyplot as plt
import numpy as np

EVENT_LENGTH = 8
PACKET_INFO_LENGTH = 12

Event = namedtuple('Event', ['type', 'subtype', 'y', 'x', 't'])
PacketInfo = namedtuple('PacketInfo', ['num_events', 'time_start', 'time_end'])


class ATISReader(object):

	def __init__(self, filename = 'date_recording.bin'):
		
		self.event_list = []
		self.InitBinaryRead(filename)

	def InitBinaryRead(self, filename):
		# Open file and print header
		self.file = open(filename, mode = 'rb')
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
				info = PacketInfo._make(struct.unpack('iii', data))
				for i in range(info.num_events):
					data = self.file.read(EVENT_LENGTH)
					self.event_list.append(Event._make(struct.unpack('BBBHH', data)))
					# Hacky stuff to have absolute time
					self.event_list[-1] = self.event_list[-1]._replace(t = self.event_list[-1].t + info.time_start)
					#raw_input() 
			except struct.error:
				print "EOF reached prematurely"
				break

	def PlotHistograms(self):
		x_distr, y_distr = zip(*[(e.x, e.y) for e in self.event_list])
		plt.subplot(2,1,1)
		plt.hist(x_distr, bins = 304)
		plt.title("X events distribution")
		plt.xlabel("Pixel X coordinate")
		plt.ylabel("Number of TD events")

		plt.subplot(2,1,2)
		plt.hist(y_distr, bins = 240)
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
		plt.hist(frequencies_combined, bins = 1000, range = (0,150))
		plt.title("Pixel frequencies, any transition")
		plt.xlabel("Frequency (Hz)")
		plt.ylabel("Number of occurences")

		plt.subplot(3,1,2)
		plt.hist(frequencies_on, bins = 1000, range = (0,150))
		plt.title("Pixel frequencies, off->on transitions")
		plt.xlabel("Frequency (Hz)")
		plt.ylabel("Number of occurences")

		plt.subplot(3,1,3)
		plt.hist(frequencies_off, bins = 1000, range = (0,150))
		plt.title("Pixel frequencies, on->off transitions")
		plt.xlabel("Frequency (Hz)")
		plt.ylabel("Number of occurences")
		plt.show()



if __name__ == '__main__':
	if len(sys.argv) == 2:
		r = ATISReader(sys.argv[1])
	else:
		r = ATISReader()
	r.ReadEvents()
	r.FrequencyAnalysis()
	r.PlotHistograms()
