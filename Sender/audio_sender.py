import threading
import wave
import pyaudio as pyaudio
import time
from Utils.utils import CLOCK_TIME
from Utils.utils import Logger

CHUNK = 1024


class Sender:
    """
    Setting things up to start the sender.
    """
    def __init__(self, file_path):
        self._is_playing = True
        self._wave_file = wave.open(file_path, 'rb')
        self._pyaudio = pyaudio.PyAudio()
        self._logger = Logger().get_instance('Sender')

    """
    It play a wav file in loop mode.
    A new thread is separated to play the sound.
    """
    def _play(self):

        stream = self._pyaudio.open(format=self._pyaudio .get_format_from_width(self._wave_file.getsampwidth()),
                                          channels=self._wave_file.getnchannels(),
                                          rate=self._wave_file.getframerate(),
                                          output=True)
        data = self._wave_file.readframes(CHUNK)

        while self._is_playing:
            stream.write(data)
            data = self._wave_file.readframes(CHUNK)
            if data == b'':
                self._wave_file.rewind()
                data = self._wave_file.readframes(CHUNK)
        stream.stop_stream()
        stream.close()
        self._wave_file.rewind()

    """
    Plays the sound for x seconds.
    """
    def _play_for_seconds(self, duration):
        self._is_playing = True
        p = threading.Thread(target=self._play)
        p.start()
        time.sleep(duration)
        self._is_playing = False
        p.join()

    """
    Protocol that indicates that a transmission will get initiated.
    """
    def start_transmition(self):
        self._logger.info('Playing sound for %f seconds indicating beginning of transmission.' % (CLOCK_TIME * 2))
        self._play_for_seconds(CLOCK_TIME * 2 + 0.1)

    def send_bit_zero(self):
        self._logger.info('Sending encoded bit 0.')
        self._play_for_seconds(CLOCK_TIME/2)
        time.sleep(CLOCK_TIME/2)

    def send_bit_one(self):
        self._logger.info('Sending encoded bit 1.')
        time.sleep(CLOCK_TIME/2)
        self._play_for_seconds(CLOCK_TIME/2)

    def close(self):
        self._logger('Closing and terminating Sender.')
        self._wave_file.close()
        self._pyaudio.terminate()










