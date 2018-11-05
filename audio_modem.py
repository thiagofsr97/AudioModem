from PhysicalLayer.Sender.audio_sender import Sender
from PhysicalLayer.Receiver.audio_receiver import Receiver
from NetworkLayer.network import Network
from Utils.utils import IP_ADDRESS_1
from Utils.utils import IP_ADDRESS_2_1
from Utils.utils import IP_ADDRESS_2_2
from Utils.utils import IP_ADDRESS_3
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
    # link = Link('101')
    # link.append_frame('101','001','1')
    network = Network(IP_ADDRESS_1)
    network.start()
    print('oiiajuxauxhauhx')
    # time.sleep(2)
    network.append_packet(IP_ADDRESS_3, IP_ADDRESS_1, '101')

    time.sleep(1000)


if __name__ == "__main__":
    main()