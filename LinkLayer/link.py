from PhysicalLayer.Sender.audio_sender import Sender
from PhysicalLayer.Receiver.audio_receiver import Receiver
import time
import threading
from Utils.utils import Logger
import crcmod
from Utils.utils import THRESHOLD

frame = ''


class Link:

    def __init__(self):
        self._crc_func = crcmod.mkCrcFun(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF)
        self._frame = ''
        self._sender = Sender('resources/beepTone.wav')
        self._receiver = Receiver()
        self._receiver.start()
        self._is_sending = True
        self._thread_collision_detection = []
        self._thread_sender = threading.Thread(target=self.send_frame)

    def _deactivate_transmission(self):
        self._is_sending = False

    def _calculate_crc(self, data_bits):
        return str(format(self._crc_func(b'%d' % int(data_bits)), "b"))

    def set_frame(self, address, data):
        self._frame = address + data + self._calculate_crc(data)


    def send_frame(self):
        if not self._receiver.is_there_transmission():
            self._thread_collision_detection = threading.Thread(target=self._receiver.has_collided,
                                                                kwargs=dict(callback=self._deactivate_transmission))
            self._thread_collision_detection.start()
            # if self._receiver.is_on():
            #     self._receiver.switch_receiver()
            self._sender.start_transmition()
            print(self._frame)
            for bit in self._frame:
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


    def clear_frame(self):
        self._frame.clear()