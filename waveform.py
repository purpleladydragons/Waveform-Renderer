import pylab
import numpy as np
import threading
import pyaudio
import random
from Tkinter import *


class Renderer(Frame):
	def __init__(self, parent,spectrum):
		Frame.__init__(self, parent, background="black")

		self.height = 800
		self.width = 1200
		self.parent = parent
		self.canvas = Canvas(parent, width=1200, height=800)
		self.bars = random.sample(xrange(0,30), 15)
		self.ind = 0
		self.s = spectrum

		self.initUI()


	def paintBars(self):
		self.canvas.delete("all")
		xs, ys = self.s.fft()
		bins = []
		for i in range(len(ys)-1):
			if i % 10 == 0:
				bins.append(sum(ys[i:i+10])/len(ys[i:i+10]))
		print len(ys), len(bins)
		for i,bar in enumerate(bins):
			if bar > 0:
				self.canvas.create_rectangle(i*10+25,self.height-200,25+i*10+10, self.height - bar - 200, fill="blue")
		self.parent.after(100, self.paintBars)
		

	def initUI(self):
		self.parent.title("Renderer")
		self.canvas.pack()
		self.paintBars()

class Spectrum:
	def __init__(self):
		self.RATE = 48100
		self.CHUNK = 1024
		self.sec_to_record = .1
		self.threads_die_now = False
		self.new_audio = False

	def close(self):
		self.p.close(self.in_stream)

	def getAudio(self):
		audioString = self.in_stream.read(self.CHUNK)
		return np.fromstring(audioString, dtype=np.int16)

	def record(self, forever=True):
		while True:
			if self.threads_die_now: break
			for i in range(self.chunksToRecord):
				self.audio[i*self.CHUNK: (i+1)*self.CHUNK]=self.getAudio()
			self.newAudio = True
			if forever==False: break

	def continuousStart(self):
		self.t = threading.Thread(target=self.record)
		self.t.start()

	def continuousEnd(self):
		self.threadsDieNow = True
	
	def setup(self):	

		self.buffersToRecord=int(self.RATE*self.sec_to_record/self.CHUNK)
		if self.buffersToRecord == 0: self.buffersToRecord = 1
		self.samplesToRecord = int(self.CHUNK*self.buffersToRecord)
		self.chunksToRecord=int(self.samplesToRecord/self.CHUNK)
		self.secPerPoint = 1.0/self.RATE
		
		self.p = pyaudio.PyAudio()

		#stream_info = pyaudio.PaMacCoreStreamInfo(
		#	flags=pyaudio.PaMacCoreStreamInfo.paMacCorePlayNice,
		#	channel_map=channel_map)

		self.in_stream = self.p.open(format=pyaudio.paInt16,
				rate = self.RATE,
				input = True,
				frames_per_buffer=self.CHUNK,
				#input_host_api_specific_stream_info = stream_info,
				channels = 1)


		self.xsBuffer=np.arange(self.CHUNK)*self.secPerPoint
		self.xs=np.arange(self.chunksToRecord*self.CHUNK) * self.secPerPoint
		self.audio = np.empty((self.chunksToRecord*self.CHUNK), dtype=np.int16)

	def downsample(self, data, mult):
		overhang = len(data)%mult
		if overhang: data=data[:-overhang]
		data = np.reshape(data, (len(data)/mult, mult))
		data = np.average(data, 1)
		return data

	def fft(self, data=None, trimBy=1, logScale = False, divBy=10000):
		if data==None:
			data = self.audio.flatten()
		left, right = np.split(np.abs(np.fft.fft(data)), 2)
		ys = np.add(left, right[::-1])
		if logScale:
		    ys=np.multiply(20,np.log10(ys))
		xs=np.arange(self.CHUNK/2,dtype=float)
		if trimBy:
		    i=int((self.CHUNK/2)/trimBy)
		    ys=ys[:i]
		    xs=xs[:i]*self.RATE/self.CHUNK
		if divBy:
		    ys=ys/float(divBy)
		return xs,ys

	def plotAudio(self):
		pylab.plot(self.audio.flatten())
		pylab.show()
def main():
	root = Tk()
	pad=3
        root.geometry("{0}x{1}+0+0".format(
            root.winfo_screenwidth()-pad, root.winfo_screenheight()-pad))
	root.geometry("550x450+300+300")
	s = Spectrum()
	s.setup()
	s.continuousStart()
	app = Renderer(root, s)


	# set up a separate thread to constantly listen to audio	
	# allow app to dig into the the audio whenever it wants
	root.after(100, app.paintBars)
	root.mainloop()


if __name__ == "__main__":
	main()

