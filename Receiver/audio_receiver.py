import pyaudio
import audioop
import threading
import time
from Utils.utils import get_logger


CLOCK_TIME = 1.0

CHANNELS=2
RATE=44100
CHUNK=1024
RECORD_SECONDS=60
THRESHOLD = 20000
FORMAT=pyaudio.paInt16
ZERO_TO_ONE = 1
ONE_TO_ZERO = 0


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
        self._byte_buffer = []
        self._bit_buffer = []
        self._logger = get_logger()



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
        self._logger.info('Idle state, waiting for transmission to start.')
        while self._is_recording:
            vol = self._get_rms()
            if vol >= THRESHOLD:
                self._logger.info('Sleeping %d seconds, protocol to start transmitting. ' % (CLOCK_TIME * 2))
                time.sleep(CLOCK_TIME*2)
                vol = self._get_rms()
                if vol >= THRESHOLD:
                    self._logger.info('Transmission has started.')
                    self._start_transmission()

    def _start_transmission(self):
        while True:
            time.sleep(CLOCK_TIME * 0.3)
            vol = self._get_rms()
            result = self._wait_for_transition(vol)
            if result != '-1':
                self._bit_buffer.append(result)
                self._logger.info('Bit read: ' + result)
            else:
                self._logger.info('Didn\'t capture transition. Returning to Idle.')
                return

    def _wait_for_transition(self, first_level):
        begin = time.time()
        after = time.time()
        while after - begin <= (CLOCK_TIME - (CLOCK_TIME * 0.3)):
            after = time.time()
            if (first_level >= THRESHOLD) and (self._get_rms() < THRESHOLD):
                self._logger.info('Found transition from noise to silence after ' + str(after-begin) + ' seconds.')
                self._resync(ZERO_TO_ONE)
                return '0'
            elif (first_level < THRESHOLD) and (self._get_rms() >= THRESHOLD):
                self._logger.info('Found transition from silence to noise after ' + str(after - begin) + ' seconds.')
                self._resync(ONE_TO_ZERO)
                return '1'
            time.sleep(CLOCK_TIME * 0.1)
        return '-1'

    def _resync(self, transition_type):
        self._logger.info('Resynchronizing. Capturing transition in a interval of %f.' % (CLOCK_TIME/2))
        if transition_type == ZERO_TO_ONE:
            begin = time.time()
            after = time.time()
            while after - begin <= (CLOCK_TIME / 2):
                after = time.time()
                if self._get_rms() >= THRESHOLD:
                    self._logger.info("Resynchronized. Shift from 0 to 1 in %f seconds" % (after - begin))
                    break
                else:
                    time.sleep(CLOCK_TIME * 0.1)
        else:
            begin = time.time()
            after = time.time()
            while after - begin <= (CLOCK_TIME / 2):
                after = time.time()
                if self._get_rms() < THRESHOLD:
                    self._logger.info("Resynchronized. Shift from 1 to 0 in %f seconds" % (after - begin))
                    break
                else:
                    time.sleep(CLOCK_TIME * 0.1)

    def get_result(self):
        return ''.join(self._bit_buffer)

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




