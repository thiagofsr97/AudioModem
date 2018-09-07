import pyaudio
import audioop
import threading
import time

CLOCK_TIME = 1.0

CHANNELS=2
RATE=44100
CHUNK=1024
RECORD_SECONDS=60
THRESHOLD = 20000
FORMAT=pyaudio.paInt16


class Receiver:
    def __init__(self):
        self._pyaudio = pyaudio.PyAudio()
        self._stream = self._pyaudio.open(format=FORMAT, channels=CHANNELS,
                                        rate=RATE, input=True, frames_per_buffer=CHUNK)
        self._is_recording = True
        self._timer = 0
        self._data = []
        self._p = threading.Thread(target=self._start)
        self._recording = threading.Thread(target=self._read_data)

    """
    This function will run in a separated thread,
    once the recording must always be in execution.
    """
    def _read_data(self):
        while self._is_recording:
            self._data = self._stream.read(CHUNK)
            # print(audioop.rms(self._data, 2))

    """
    It returns the level of the audio using RMS measure.
    Print this value if you need to check the differences
    between noise and silence in order to define your THRESHOLD.
    """
    def _get_rms(self):
        if self._data:
            return audioop.rms(self._data, 2)
        else:
            return 0

    def _start(self):
        print('Idle state... Waiting for transmission.')
        while self._is_recording:
            vol = self._get_rms()
            if vol >= THRESHOLD:
                passed = True
                print("----------------Sleeeping %d seconds ------------------" % (CLOCK_TIME * 2))
                time.sleep(CLOCK_TIME*2)
                vol = self._get_rms()
                if vol >= THRESHOLD:
                    passed = True
                else:
                    passed = False
                if passed:
                    print('----------Starting Transmission---------')
                    self._start_transmission()


    def _start_transmission(self):
        while True:
            print('------Reading bits------')
            time.sleep(CLOCK_TIME * 0.3)
            vol = self._get_rms()
            result = self._wait_for_transition(vol)
            if result != '-1':
                print('Bit read: ' + result)
            else:
                print('Didn\'t capture transition. Returning to Idle.')
                return

    def _wait_for_transition(self, first_level):
        sucess = False
        if first_level >= THRESHOLD:
            begin = time.time()
            after = time.time()
            while after - begin < (CLOCK_TIME - (CLOCK_TIME * 0.3)):
                after = time.time()

                if self._get_rms() < THRESHOLD:
                    print('Found transition after ' + str(after-begin) + ' seconds.')
                    time.sleep((CLOCK_TIME/2))
                    return '0'
                time.sleep(CLOCK_TIME * 0.1)

        elif first_level < THRESHOLD:
            begin = time.time()
            after = time.time()
            while after - begin < (CLOCK_TIME - (CLOCK_TIME * 0.3)):
                after = time.time()
                if self._get_rms() >= THRESHOLD:
                    print('Found transition after ' + str(after - begin) + ' seconds.')
                    time.sleep((CLOCK_TIME/2))
                    return '1'
                time.sleep(CLOCK_TIME * 0.1)
        return '-1'



    def start(self):
        self._recording.start()
        self._p.start()


    def shutdown(self):
        self._is_recording = False
        self._recording.join()
        self._p.join()
        self._stream.stop_stream()
        self._stream.close()
        self._pyaudio.terminate()




