from PhysicalLayer.Sender.audio_sender import Sender
from PhysicalLayer.Receiver.audio_receiver import Receiver
import time
import threading
from Utils.utils import Logger
import crcmod
from Utils.utils import PC_ADDRESS
from Utils.utils import FRAME_FLAG
from Utils.utils import N_ATTEMPTIVES
from queue import Queue

class Link:

    def __init__(self):
        self._logger = Logger().get_instance('LinkLayer')
        self._crc_func = crcmod.mkCrcFun(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF)
        self._queue_buffer_receiver = Queue(100)
        self._queue_frame_buffer = Queue(100)
        self._is_sending = True
        self._thread_collision_detection = []
        self._receiver = Receiver()
        self._receiver.start()
        self._sender = Sender('resources/beepTone.wav')
        self._thread_sender = threading.Thread(target=self._send_frame)
        self._thread_sender.start()

    def _transmission_reader(self):
        bit = self._receiver.read_bit()
        if bit == FRAME_FLAG:
            frame = []
            bit = self._receiver.read_bit()
            if bit == PC_ADDRESS:
                while bit != FRAME_FLAG:
                    frame.append(bit)
                    bit = self._receiver.read_bit()
                if self._check_frame(frame):
                    self._queue_buffer_receiver.put(frame)
                else:
                    self._append_control_frame('1')
                frame.clear()

    def _check_frame(self, frame):
        if len(frame) < 34:
            return False
        else:
            crc_bits = frame[-32:]
            data_bits = frame[1:len(frame)-32]
            if crc_bits != self._calculate_crc(''.join(data_bits)):
                return False

        return True

    def _deactivate_transmission(self):
        self._is_sending = False

    def _calculate_crc(self, data_bits):
        return str(format(self._crc_func(b'%d' % int(data_bits)), "b"))

    def append_frame(self, address, data):
        frame = address + data + self._calculate_crc(data)
        self._queue_frame_buffer.put(frame)

    def _append_control_frame(self, address):
        frame = address + '111'
        self._queue_frame_buffer.put(frame)

    def _send_frame(self):
        while True:
            frame = self._queue_frame_buffer.get()
            self._logger.info('Sending frame: [[' + frame[0] + ']['
                              + frame[1:len(frame)-32] + '][' + frame[-32:] + ']].')

            timeout = 0.5
            self._logger.info('Making first attempt of transmitting the frame.')
            sucess = self._send_attemptive(frame)
            if not sucess:
                for i in range(1, N_ATTEMPTIVES):
                    self._logger.info('Attempt %d of transmitting the frame.' % (i+1))
                    if self._send_attemptive(frame, timeout=timeout):
                        break
                    else:
                        if i + 1 == N_ATTEMPTIVES:
                            self._logger.info('Number of attemps reached, aborting transmission.')
                        timeout=timeout*2

    def _send_attemptive(self, frame, timeout=None):
        while self._receiver.is_there_transmission():
            pass
            # self._logger.info('Waiting for silence in order to transmit.')

        self._is_sending = True
        self._thread_collision_detection = threading.Thread(target=self._receiver.has_collided,
                                                            kwargs=dict(callback=self._deactivate_transmission))
        self._thread_collision_detection.start()
        # if self._receiver.is_on():
        #     self._receiver.switch_receiver()
        if timeout:
            self._logger.info('Sleeping for %d seconds before trying to send the frame.' % timeout)
            time.sleep(timeout)
        self._sender.start_transmition()
        for bit in frame:
            if self._is_sending:
                if bit == '1':
                    self._sender.send_bit_one()
                else:
                    self._sender.send_bit_zero()
            else:
                break
        if self._is_sending:
            self._sender.end_transmition()
        # self._receiver.switch_receiver()
        self._receiver.detector_flag()
        self._thread_collision_detection.join()
        if not self._is_sending:
            return False
        return True
