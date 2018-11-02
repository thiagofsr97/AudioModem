#Eng Eder de Souza 01/12/2011
#ederwander
from matplotlib.mlab import find
import numpy as np
import math
import pyaudio


chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 20


def Pitch(signal):
    signal = np.fromstring(signal, 'Int16')
    crossing = [math.copysign(1.0, s) for s in signal]
    index = find(np.diff(crossing))
    f0=round(len(index) *RATE /(2*np.prod(len(signal))))
    return f0


p = pyaudio.PyAudio()

stream = p.open(format = FORMAT,
channels = CHANNELS,
rate = RATE,
input = True,
output = True,
frames_per_buffer = chunk)

while True:
    data = stream.read(chunk)
    Frequency = Pitch(data)
    print("%f Frequency" % Frequency)