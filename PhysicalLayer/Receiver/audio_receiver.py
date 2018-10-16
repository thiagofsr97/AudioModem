import pyaudio
import audioop
import threading
import time
from Utils.utils import Logger
from Utils.utils import CLOCK_TIME
from Utils.utils import THRESHOLD

CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 60

FORMAT = pyaudio.paInt16
ZERO_TO_ONE = 10
ONE_TO_ZERO = 5
BIT_ZERO = 0
BIT_ONE = 1
FRAME_FLAG = -1
K_SYMBOL = -2
BUFFER_SIZE = 100


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
        self._bit_buffer = ['-1'] * BUFFER_SIZE
        self._logger = Logger().get_instance('Receiver')
        self._fill_count = threading.Semaphore(0)
        self._empty_count = threading.Semaphore(BUFFER_SIZE)
        self._front = 0
        self._rear = 0
        self._detector_flag = True


    """
    This function will run in a separated thread,
    once the recording must always be in execution.
    """
    def _read_data(self):
        while self._is_recording:
            self._data = self._stream.read(CHUNK)

    """
    It returns the level of the audio using RMS measure.
    Print this value if you need to check the differences
    between noise and silence in order to define your THRESHOLD.
    """

    def _get_rms(self):
        if self._data:
            vol = audioop.rms(self._data, 2)
            # print(vol)
            return vol
        else:
            return 0

    """
    Wait for a transition from silence to noise. If it stays for 
    twice the clock time in this state, the transmission 
    will get started.
    """

    def _start(self):

        self._logger.info('Idle state, waiting for transmission to start.')
        while self._is_receiving:
            vol = self._get_rms()
            if vol >= THRESHOLD:
                self._logger.info('Sleeping %f seconds, protocol to start transmitting. ' % (CLOCK_TIME))
                time.sleep(CLOCK_TIME)
                vol = self._get_rms()
                if vol >= THRESHOLD:
                    self._logger.info('Transmission has started. Frame Flag detected.')
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
            result = self._wait_for_transition(vol)
            if result != FRAME_FLAG and result != K_SYMBOL:
                # self._bit_buffer.append(result)
                self._append_bit(str(result))
                self._logger.info('Bit read: ' + str(result))
            elif result == FRAME_FLAG:
                self._logger.info('FRAME FLAG detected. Closing frame and resetting state.')
                return
            else:
                exit(1)

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
        to_return = FRAME_FLAG
        while after - begin <= (CLOCK_TIME - (CLOCK_TIME * 0.3)):
            after = time.time()
            if (first_level >= THRESHOLD) and (self._get_rms() < THRESHOLD):
                self._logger.info('Found transition from noise to silence after ' + str(after-begin) + ' seconds.')
                self._resync(ZERO_TO_ONE)
                return BIT_ZERO
            elif (first_level < THRESHOLD) and (self._get_rms() >= THRESHOLD):
                self._logger.info('Found transition from silence to noise after ' + str(after - begin) + ' seconds.')
                self._resync(ONE_TO_ZERO)
                return BIT_ONE
            elif (first_level >= THRESHOLD) and (self._get_rms() >= THRESHOLD):
                to_return = FRAME_FLAG
            elif (first_level < THRESHOLD) and (self._get_rms() < THRESHOLD):
                to_return = K_SYMBOL

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
        self._logger.info('Trying to resynchronize. Capturing transition in a interval of %f. seconds' % (CLOCK_TIME/2))
        if transition_type == ZERO_TO_ONE:
            begin = time.time()
            after = time.time()
            while after - begin <= (CLOCK_TIME / 2):
                if self._get_rms() >= THRESHOLD:
                    self._logger.info("Resynchronized. Shift from 0 to 1 in %f seconds" % (after - begin))
                    break
                # else:
                #     time.sleep(CLOCK_TIME * 0.1)
                after = time.time()
        else:
            begin = time.time()
            after = time.time()
            while after - begin <= (CLOCK_TIME / 2):
                if self._get_rms() < THRESHOLD:
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
        self._front = (self._front + 1) % BUFFER_SIZE

    """
    By using synchronization with semaphores, bits are read one by one.
    Must be used in a separated thread, otherwise other processes might be blocked. 
    """
    def read_bit(self):
        self._fill_count.acquire()
        bit = self._bit_buffer[self._rear]
        self._empty_count.release()
        self._rear = (self._rear + 1) % BUFFER_SIZE
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
            if self._get_rms() >= THRESHOLD * 2:
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
            if vol >= THRESHOLD:
                return True
        return False


