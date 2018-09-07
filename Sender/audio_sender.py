import threading
import wave
import pyaudio as pyaudio
import time

CHUNK = 1024


class Sender:
    def __init__(self, file_path):
        self._is_playing = True
        self._wave_file = wave.open(file_path, 'rb')
        self._pyaudio = pyaudio.PyAudio()

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

    def play(self, duration):
        self._is_playing = True
        p = threading.Thread(target=self._play)
        p.start()
        time.sleep(duration)
        self._is_playing = False
        p.join()

    def close(self):
        self._wave_file.close()
        self._pyaudio.terminate()










