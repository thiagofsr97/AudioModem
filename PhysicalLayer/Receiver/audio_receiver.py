import pyaudio
import audioop
import threading
import time
from matplotlib.mlab import find
import numpy as np
import math
from Utils.utils import Logger
from Utils.utils import CLOCK_TIME
from Utils.utils import THRESHOLD
from Utils.utils import EMPTY
from Utils.utils import K_SYMBOL
from Utils.utils import FRAME_FLAG
from Utils.utils import BUFFERSIZE
from Utils.utils import THRESHOLD_HIGH
from Utils.utils import THRESHOLD_LOW
from statistics import mode

CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 60

FORMAT = pyaudio.paInt16
ZERO_TO_ONE = 10
ONE_TO_ZERO = 5
BIT_ZERO = 0
BIT_ONE = 1

class Receiver:
    """
    Setting things up in order to start the receiver.
    """

    def __init__(self):
        self._pyaudio = pyaudio.PyAudio()
        self._stream = self._pyaudio.open(format=FORMAT, channels=CHANNELS,
                                          rate=RATE, input=True, frames_per_buffer=CHUNK)
        self._is_recording = True
        self._is_receiving = True
        self._timer = 0
        self._data = []
        self._p = threading.Thread(target=self._start)
        self._recording = threading.Thread(target=self._read_data)
        self._bit_buffer = [str(EMPTY)] * BUFFERSIZE
        self._logger = Logger().get_instance('Receiver')
        self._fill_count = threading.Semaphore(0)
        self._empty_count = threading.Semaphore(BUFFERSIZE)
        self._front = 0
        self._rear = 0
        self._detector_flag = True
        self._half_clock = CLOCK_TIME / 2
        self._frequency = 0
        self._previous = None

    def _pitch(self, signal):
        signal = np.fromstring(signal, 'Int16')
        crossing = [math.copysign(1.0, s) for s in signal]
        index = find(np.diff(crossing))
        f0 = round(len(index) * RATE / (2 * np.prod(len(signal))))
        return f0

    """
    This function will run in a separated thread,
    once the recording must always be in execution.
    """

    def _read_data(self):
        buffer_ = []
        frequency = 0
        while self._is_recording:
            for i in range(0, 4):
                self._data = self._stream.read(CHUNK)
                if self._data:
                    frequency = self._pitch(self._data)
                    # print(self._frequency, 'hz....')
                else:
                    frequency = 0
                buffer_.append(frequency)

            try:
                self._frequency = mode(buffer_)
            except:
                self._frequency = max(buffer_)
            # print(self._frequency)
            buffer_.clear()
    """
    It returns the level of the audio using RMS measure.
    Print this value if you need to check the differences
    between noise and silence in order to define your THRESHOLD.
    """

    def _get_rms(self):
        freq = self._frequency
        # print(freq)

        if (freq < (THRESHOLD_HIGH + 30)) and (freq > (THRESHOLD_HIGH - 10)):
            return THRESHOLD_HIGH
        elif(freq < (THRESHOLD_LOW + 30)) and (freq > (THRESHOLD_LOW - 10)):
            return THRESHOLD_LOW
        return freq
        # if freq > THRESHOLD_HIGH - 30:
        #     return THRESHOLD_HIGH
        # return THRESHOLD_LOW

    """
    Wait for a transition from silence to noise. If it stays for 
    twice the clock time in this state, the transmission 
    will get started.
    """

    def _start(self):

        self._logger.info('Idle state, waiting for transmission to start.')
        while self._is_receiving:
            vol = self._get_rms()
            # print(vol)
            begin = time.time()
            if vol == THRESHOLD_HIGH:
                after = time.time()
                remaining_clock_time = CLOCK_TIME * 2
                self._logger.info('Sleeping %f seconds, protocol to start transmitting. ' % (CLOCK_TIME * 2))
                is_ok = True
                while after-begin <= remaining_clock_time-0.01:
                    after = time.time()
                    vol = self._get_rms()
                    if not vol == THRESHOLD_HIGH:
                        is_ok = False
                        break
                if is_ok:
                    self._logger.info('Transmission has started. Frame Flag detected.')
                    self._append_bit(str(FRAME_FLAG))
                    self._initiate_transmission()

    """
    Starts the transmission of bits by using Manchester Encoding.
    Once initiated, the recorder sleeps for 30% of the CLOCK_TIME in
    order to the get the first sample of RMS measure, so it gets the
    first level (noise or silence). After that, it will wait for a 
    transition of level, identifying if the encoded information is
    representing the bit 1 or 0.
    """

    def _initiate_transmission(self):
        while True:
            time.sleep(CLOCK_TIME * 0.3)
            vol = self._get_rms()
            self._logger.info('Detected %f herz as first level.' % vol)
            result = self._wait_for_transition(vol)

            if result != FRAME_FLAG and result != K_SYMBOL:
                # self._bit_buffer.append(result)
                self._append_bit(str(result))
                self._logger.info('Bit read: ' + str(result))
            elif result == FRAME_FLAG:
                print("(_initiate_transmission)String recebida: ", str("".join(self._bit_buffer)))
                self._append_bit(str(FRAME_FLAG))
                self._logger.info('FRAME FLAG detected. Closing frame and returning to initial state.')
                return
            else:
                self._logger.info('K Symbol found. Returning to initial state.')
                return

    """
    Waits for a transition of levels occurs, representing the information encoded
    according to Manchester Enconding.
        Silence to Noise --> Bit 1
        Noise to Silence --> Bit 0

    The sender has the interval of 70% of the Clock Time to send its transition.
    This amount of time helps both receiver and sender to stay synchronized, as 
    well as it stablishes a interval that once reached, tells the receiver that no 
    bits is being transmitted.
        Noise for 1 Clock Time --> J symbol
        Silence for 1 Clock Time --> K symbol

    Return:
        1 or 0, if bits has been decoded.
        -1 if no bit has been decoded.
    """

    def _wait_for_transition(self, first_level):
        begin = time.time()
        after = time.time()
        to_return = K_SYMBOL
        remaining_clock_time = (CLOCK_TIME - (CLOCK_TIME * 0.3))

        while after - begin <= remaining_clock_time:
            after = time.time()
            current_rms = self._get_rms()
            if (first_level == THRESHOLD_LOW) and (current_rms > THRESHOLD_LOW + 100):
                self._logger.info('Found transition from noise to silence after ' + str(after - begin) + ' seconds.')
                self._resync(ONE_TO_ZERO)
                self._logger.info('Detected %f hertz as second level.' % current_rms)
                return BIT_ZERO
            elif (first_level == THRESHOLD_HIGH) and (current_rms < THRESHOLD_HIGH - 100):
                self._logger.info('Found transition from silence to noise after ' + str(after - begin) + ' seconds.')
                self._resync(ZERO_TO_ONE)
                self._logger.info('Detected %f hertz as second level.' % current_rms)
                return BIT_ONE
            elif (first_level == THRESHOLD_HIGH) and (current_rms == THRESHOLD_HIGH):
                # print("elif 2 First level {} e rms atual {}.".format(first_level, current_rms))
                to_return = FRAME_FLAG
            elif (first_level == THRESHOLD_LOW) and (current_rms == THRESHOLD_LOW):
                # print("elif 3First level {} e rms atual {}.".format(first_level, current_rms))
                to_return = K_SYMBOL
            time.sleep(0.1)
        self._logger.info('Detected % hertz as second level.' % current_rms)
        return to_return

    """
    Once a transition has occurred, it means that the receiver is supposedly at half of the Clock Time. 
    (Time when transition occurs).
    In order to get a new sample, it needs to wait for the other 
    half of Clock Time at most, so it can do it all over again. For matters of synchronization, this
    time might no be precised. So after decoding a new bit of information, the receiver will wait
    for a new transition in the interval of (Clock Time/2) seconds, indicating the start of a new bit.
    If the transition doesn't occur in this interval, it means the next bit is different from the previous one.
    """

    def _resync(self, transition_type):

        self._logger.info(
            'Trying to resynchronize. Capturing transition in a interval of %f. seconds' % self._half_clock)
        begin = time.time()
        after = time.time()

        current_rms = self._get_rms()

        if transition_type == ZERO_TO_ONE:
            while after - begin <= self._half_clock:
                if current_rms == THRESHOLD_HIGH:
                    self._logger.info("Resynchronized. Shift from 0 to 1 in %f seconds" % (after - begin))
                    break
                # else:
                #     time.sleep(CLOCK_TIME * 0.1)
                after = time.time()
        else:
            while after - begin <= self._half_clock:
                if current_rms == THRESHOLD_LOW:
                    self._logger.info("Resynchronized. Shift from 1 to 0 in %f seconds" % (after - begin))
                    break
                # else:
                #     time.sleep(CLOCK_TIME * 0.1)
                after = time.time()

    """
    With the usage of a buffer of limited size, bits will be appended
    by using semaphores to keep writing and reading synchronized.
    """

    def _append_bit(self, bit):
        self._empty_count.acquire()
        self._bit_buffer[self._front] = bit
        self._fill_count.release()
        self._front = (self._front + 1) % BUFFERSIZE


    """
    By using synchronization with semaphores, bits are read one by one.
    Must be used in a separated thread, otherwise other processes might be blocked. 
    """

    def read_bit(self):
        self._fill_count.acquire()
        bit = self._bit_buffer[self._rear]
        self._empty_count.release()
        self._rear = (self._rear + 1) % BUFFERSIZE
        return bit

    """
    It gets the receiver started in a different thread.
    """

    def start(self):
        self._recording.start()
        self._p.start()

    """
    Stops the threads and closes the recorder.

    """

    def shutdown(self):
        self._logger.info('Shutting down physical layer.')
        self._is_recording = False
        self._recording.join()
        self._p.join()
        self._stream.stop_stream()
        self._stream.close()
        self._pyaudio.terminate()

    def switch_receiver(self):
        if self._is_recording:
            self._is_receiving = False
            self._p.join()
            self._logger.info('Receiver has been paused, not getting any audio data.')
        else:
            self._p = threading.Thread(target=self._start)
            self._is_receiving = True
            self._p.start()
            self._logger.info('Receiver has been restarted, getting audio data.')

    def is_on(self):
        return self._is_receiving

    def has_collided(self, callback=None):
        self._detector_flag = True
        while self._detector_flag:
            vol = self._get_rms()
            # print(vol)
            if vol >= THRESHOLD * 2:
                self._logger.info('Collision has been detected. Abborting...')
                if callback:
                    callback()
                    break
            time.sleep(CLOCK_TIME * 0.1)

    def detector_flag(self):
        self._detector_flag = False

    def is_there_transmission(self):
        begin = time.time()
        after = time.time()
        while after - begin <= (CLOCK_TIME * 0.3):
            after = time.time()
            vol = self._get_rms()
            if vol == THRESHOLD_HIGH or vol == THRESHOLD_LOW:
                return True
        return False


