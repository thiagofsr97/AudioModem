from PhysicalLayer.Sender.audio_sender import Sender
from PhysicalLayer.Receiver.audio_receiver import Receiver
from LinkLayer.link import Link
import time
import threading
bits = []


def read_bits(times, receiver=Receiver()):
    for i in range(0, times):
        bit = receiver.read_bit()
        bits.append(bit)
        print('BIT RECEIVED: ' + bit)


def main():
    linkLayer = Link(0,True)
    time.sleep(2)
    linkLayer.append_frame('1', '1')
    # linkLayer.shutdown()

if __name__ == "__main__":
    main()