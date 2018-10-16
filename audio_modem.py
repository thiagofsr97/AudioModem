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
    # sender = Sender('resources/beepTone.wav')
    # # sender2 = Sender('resources/beepTone.wav')
    #
    # receiver = Receiver()
    # receiver.start()
    #
    # """
    # Initiating the sender 5 seconds later
    # """
    # time.sleep(2)
    #
    # """
    # starting protocol
    # """
    # sender.start_transmition()
    # # sender2.start_transmition()
    #
    # string_bits = '01101011110000'
    # p = threading.Thread(target=read_bits, args=(len(string_bits), receiver))
    # p.start()
    # for bit in string_bits:
    #     if bit == '1':
    #         sender.send_bit_one()
    #         # sender2.send_bit_one()
    #
    #     else:
    #         sender.send_bit_zero()
    #         # sender2.send_bit_zero()
    # receiver.shutdown()
    # p.join()
    # result = ''.join(bits)
    # if string_bits == result:
    #     print("Bits sent: " + string_bits)
    #     print("Bits received: " + result)
    #     print("The bits matched.")
    # else:
    #     print("The bits didn\'t matched.")
    # # try:
    # #     while 1:
    # #         time.sleep(.1)
    # # except KeyboardInterrupt:
    # #     receiver.shutdown()
    # #     thread_,join()
    #
    linkLayer = Link()
    time.sleep(0.5)
    linkLayer.set_frame('1','01010101010111110')
    linkLayer.send_frame()
if __name__ == "__main__":
    main()