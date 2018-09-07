from Sender.audio_sender import Sender
from Receiver.audio_receiver import Receiver
import time

CLOCK_TIME = 1.0

def main():
    sender = Sender('resources/beepTone.wav')
    receiver = Receiver()
    receiver.start()

    time.sleep(1)

    """
    starting protocol
    """
    sender.play(CLOCK_TIME * 2)

    string_bits = '001001'
    for bit in string_bits:
        if bit == '1':
            time.sleep(CLOCK_TIME/2)
            sender.play(CLOCK_TIME/2)

        else:
            sender.play(CLOCK_TIME/2)
            time.sleep(CLOCK_TIME/2)

    receiver.shutdown()
    # try:
    #     while 1:
    #         time.sleep(.1)
    # except KeyboardInterrupt:
    #     receiver.shutdown()
    #     thread_,join()





if __name__ == "__main__":
    main()