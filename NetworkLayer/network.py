from LinkLayer.link import Link
from Utils.utils import Logger
from Utils.utils import PC_ADDRESS_1
from Utils.utils import BUFFERSIZE
from Utils.utils import PC_ADDRESS_2
from Utils.utils import ROUTING_TABLE_2
import threading

from queue import Queue

IP_BITS_LENGHT = 8


class Network:
    def __init__(self, ip_address, ip_address_2=None):
        self._pc_address = PC_ADDRESS_1
        self._linker = None
        self._logger = Logger().get_instance('NetworkLayer')
        self._queue_sender = Queue(BUFFERSIZE)
        self._queue_reader = Queue(BUFFERSIZE)
        self._ip_address = ip_address
        self._ip_address_2 = ip_address_2
        self._is_gateway = True if ip_address_2 else False
        self._is_reading_packets = True
        self._is_sending_packets = True
        self._thread_reader = None
        self._thread_sender = None
        self._routing_table = ROUTING_TABLE_2


    def start(self):
        self._linker = Link(self._pc_address)
        self._linker.start()
        self._logger.info('Initiating network layer...')
        self._thread_sender = threading.Thread(target=self._send_packet)
        self._thread_reader = threading.Thread(target=self._read_packet)
        self._thread_sender.start()
        self._thread_reader.start()


    def shutdown(self):
        self._is_sending_packets = False
        self._is_reading_packets = False
        self._queue_sender.put('')
        self._queue_reader.put('')
        if self._linker:
            self._linker.shutdown()
        if self._thread_reader and self._thread_reader.is_alive():
            self._thread_reader.join()
        if self._thread_sender and self._thread_reader.is_alive():
            self._thread_sender.join()
        print(threading.enumerate())


    def _convert_ip_bin(self, ip):
        ip = ip.split('.')
        return '{0:04b}{1:04b}'.format(int(ip[0]), int(ip[1]))

    def append_packet(self, dest_ip, source_ip, data):
        self._logger.info('Adding packet to sender queue. Source IP: %s Destination IP: %s.' % (dest_ip, source_ip))
        self._queue_sender.put([PC_ADDRESS_2, self._pc_address, self._convert_ip_bin(dest_ip)+self._convert_ip_bin(source_ip)+data])

    def read_packet(self):
        packet = self._queue_reader.get()
        if packet == '':
            return None
        return packet

    def _send_packet(self):
        while self._is_sending_packets:
            packet = self._queue_sender.get()
            if not self._is_sending_packets:
                break
            self._logger.info('Sending packet over link layer.  Packet: | %s | %s | %s | %s | %s |' %
                              (packet[0], packet[1], packet[2][0:IP_BITS_LENGHT],
                               packet[2][IP_BITS_LENGHT:IP_BITS_LENGHT*2],
                               packet[2][IP_BITS_LENGHT*2:]))
            self._linker.append_frame(packet[0], packet[1], packet[2])
        self._logger.info('Packet sender deactivated.')

    def _read_packet(self):
        while self._is_reading_packets:
            dest_mac, source_mac, data, crc = self._linker.get_frame()
            if not self._is_reading_packets:
                break
            dest_ip = data[0:IP_BITS_LENGHT]
            source_ip = data[IP_BITS_LENGHT:IP_BITS_LENGHT*2]
            self._logger.info('Reading frame received from link layer... Packet: | %s | %s | %s | %s | %s | %s |' %
                              (dest_mac, source_mac, dest_ip, source_ip, data[IP_BITS_LENGHT*2:], crc))
            if (dest_ip == self._convert_ip_bin(self._ip_address)) or (self._ip_address_2 and dest_ip == self._convert_ip_bin(self._ip_address_2)):
                self._logger.info('Destination ip is referring to this host. Packet being stored in Network Storaged.')
                self._queue_reader.put([dest_mac, source_mac, dest_ip, source_ip, data, crc])
            else:
                mac_address = None
                if self._is_gateway:
                    for row in self._routing_table:
                        if self._convert_ip_bin(row[0]) == dest_ip:
                            mac_address = row[3]
                            self._logger('Destination ip found in routing table. Sending packet over to Host of MacAddress: %s...' % mac_address)
                            dest_mac = mac_address
                            source_mac = self._pc_address
                            self._queue_sender.put([dest_mac, source_mac, dest_ip + source_ip + data + crc])

                    if not mac_address:
                        self._logger.error('Destination ip %d.%d not found in routing table... Dispatching packet.' %
                                           (int(dest_ip[0:IP_BITS_LENGHT], 2), int(dest_ip[IP_BITS_LENGHT:IP_BITS_LENGHT*2], 2)))

                else:
                    self._logger.error('Packet read couldn\'t be redirected. Dispatching it...')