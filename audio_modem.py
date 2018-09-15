from Sender.audio_sender import Sender
from Receiver.audio_receiver import Receiver
import time
import threading
bits = []


def read_bits(times, receiver=Receiver()):
    for i in range(0, times):
        bit = receiver.read_bit()
        bits.append(bit)
        print('BIT RECEIVED: ' + bit)


def main():

    sender = Sender('resources/beepTone.wav')
    receiver = Receiver()
    receiver.start()

    """
    Initiating the sender 5 seconds later
    """
    time.sleep(5)

    """
    starting protocol
    """
    sender.start_transmition()

    string_bits = '01001001000000001111111111010101010000'
    p = threading.Thread(target=read_bits, args=(len(string_bits), receiver))
    p.start()
    for bit in string_bits:
        if bit == '1':
            sender.send_bit_one()

        else:
            sender.send_bit_zero()

    receiver.shutdown()
    p.join()
    result = ''.join(bits)
    if string_bits == result:
        print("Bits sent: " + string_bits)
        print("Bits received: " + result)
        print("The bits matched.")
    else:
        print("The bits didn\'t matched.")
    # try:
    #     while 1:
    #         time.sleep(.1)
    # except KeyboardInterrupt:
    #     receiver.shutdown()
    #     thread_,join()


if __name__ == "__main__":
    main()