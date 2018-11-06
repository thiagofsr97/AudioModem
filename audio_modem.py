from PhysicalLayer.Sender.audio_sender import Sender
from PhysicalLayer.Receiver.audio_receiver import Receiver
from NetworkLayer.network import Network
from Utils.utils import IP_ADDRESS_1
from Utils.utils import IP_ADDRESS_2_1
from Utils.utils import IP_ADDRESS_2_2
from Utils.utils import IP_ADDRESS_3

import signal
import sys
import time
bits = []

network = None
def read_bits(times, receiver=Receiver()):
    for i in range(0, times):
        bit = receiver.read_bit()
        bits.append(bit)
        print('BIT RECEIVED: ' + bit)

def signal_handler(signal, frame):
    network.shutdown()

def main():
    global network
    network = Network(IP_ADDRESS_2_1, IP_ADDRESS_2_2)
    network.start()
    # network.append_packet('10.12', '12.4','1')
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    main()