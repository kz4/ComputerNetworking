import argparse
import sys
import socket
import struct
import time

from network import *
from random import randint
from collections import namedtuple, OrderedDict
from util import checksum

# Constants
SYN = 0 + (1 << 1) + (0 << 2) + (0 << 3) + (0 << 4) + (0 << 5)
ACK = 0 + (0 << 1) + (0 << 2) + (0 << 3) + (1 << 4) + (0 << 5)
SYN_ACK = 0 + (1 << 1) + (0 << 2) + (0 << 3) + (1 << 4) + (0 << 5)
FIN = 1 + (0 << 1) + (0 << 2) + (0 << 3) + (0 << 4) + (0 << 5)
FIN_ACK = 1 + (0 << 1) + (0 << 2) + (0 << 3) + (1 << 4) + (0 << 5)
PSH_ACK = 0 + (0 << 1) + (0 << 2) + (1 << 3) + (1 << 4) + (0 << 5)

TCP_HDR_FMT = '!HHLLBBHHH'
PSH_FMT = '!4s4sBBH'
TCPSeg = namedtuple(
    'TCPSeg', 'tcp_source tcp_dest tcp_seq tcp_ack_seq tcp_check data tcp_flags tcp_adwind')

class Tcp(object):
    def __init__(self, source_ip, destination_ip, destination_components, destination_port):
        self.destination_ip = destination_ip
        self.destination_port = destination_port
        self.source_ip = source_ip
        self.local_port = randint(1001, 65535)
        self.send_buf = ''
        self.recv_buf = ''
        self.tcp_seq = 0
        self.tcp_ack_seq = 0
        self.ip_id = 0
        self.status = ''
        self.adwind_size = 2048
        self.ip = Ip(source_ip, destination_ip)
        self.http_request = ''
        
    def set_request(self, requst_str):
        self.http_request = requst_str

    def pack_tcp_segment(self, payload='', flags=ACK):
        """
        Generate TCP segment.
        """
        # tcp header fields
        tcp_source = self.local_port   # source port
        tcp_dest = self.destination_port   # destination port
        tcp_seq = self.tcp_seq
        tcp_ack_seq = self.tcp_ack_seq
        tcp_doff = 5  # 4 bit field, size of tcp header, 5 * 4 = 20 bytes
        tcp_window = self.adwind_size  # maximum allowed window size
        tcp_check = 0
        tcp_urg_ptr = 0
        tcp_offset_res = (tcp_doff << 4) + 0
        tcp_flags = flags
        tcp_header = struct.pack(TCP_HDR_FMT, tcp_source, tcp_dest, tcp_seq,
                                 tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)

        # pseudo header fields
        source_address = socket.inet_aton(self.source_ip)
        dest_address = socket.inet_aton(self.destination_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        if len(payload) % 2 != 0:
            payload += ' '
        tcp_length = len(tcp_header) + len(payload)

        psh = struct.pack(PSH_FMT, source_address, dest_address, placeholder,
                          protocol, tcp_length)
        psh = psh + tcp_header + payload

        tcp_check = checksum(psh)
        tcp_header = struct.pack(TCP_HDR_FMT[:-2], tcp_source, tcp_dest,
                                 tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + \
            struct.pack('H', tcp_check) + struct.pack('!H', tcp_urg_ptr)

        return tcp_header + payload

    def unpack_tcp_segment(self, segment):
        """
        Parse TCP segment
        """
        tcp_header_size = struct.calcsize(TCP_HDR_FMT)
        hdr_fields = struct.unpack(TCP_HDR_FMT, segment[:tcp_header_size])
        tcp_source = hdr_fields[0]
        tcp_dest = hdr_fields[1]
        tcp_seq = hdr_fields[2]
        tcp_ack_seq = hdr_fields[3]
        tcp_doff_resvd = hdr_fields[4]
        tcp_doff = tcp_doff_resvd >> 4  # get the data offset
        tcp_adwind = hdr_fields[6]
        old_tcp_check = hdr_fields[7]
        tcp_urg_ptr = hdr_fields[8]
        # parse TCP flags
        tcp_flags = hdr_fields[5]
        # process the TCP options if there are
        # currently just skip it
        if tcp_doff > 5:
            opts_size = (tcp_doff - 5) * 4
            tcp_header_size += opts_size
        # get the TCP data
        data = segment[tcp_header_size:]
        # compute the checksum of the recv packet with psh
        tcp_check = self._tcp_check(segment)
        tcp_check = 0
        return TCPSeg(tcp_seq=tcp_seq, 
            tcp_source=tcp_source, 
            tcp_dest=tcp_dest, 
            tcp_ack_seq=tcp_ack_seq,
            tcp_adwind=tcp_adwind,
            tcp_flags=tcp_flags, tcp_check=tcp_check, data=segment[tcp_header_size:])

    def _tcp_check(self, payload):
        """
        checksum on received TCP packet.
        """
        # pseudo header fields
        source_address = socket.inet_aton(self.source_ip)
        dest_address = socket.inet_aton(self.destination_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(payload)

        psh = struct.pack(PSH_FMT, source_address, dest_address,
                          placeholder, protocol, tcp_length)
        psh = psh + payload

        return checksum(psh)

    def _send(self, data='', flags=ACK):
        """
        Send packed TCP packets to next layer
        """
        self.send_buf = data
        tcp_segment = self.pack_tcp_segment(data, flags=flags)
        # ip_packet = self.ip.pack_ip_packet(tcp_segment)
        # self.ssocket.sendto(ip_packet, (self.destination_ip, self.destination_port))
        self.ip.send(tcp_segment, (self.destination_ip, self.destination_port))

    def send(self, data):
        """
        Prepare data and send it to next layer
        """
        self._send(data, flags=PSH_ACK)

        while not self.recv_ack():
            self._send(data, flags=PSH_ACK)

        # reset send_buf
        self.send_buf = ''

##    def _recv(self, size=65535, delay=60):
##        """
##        Receive data from next layer
##        """
##        self.rsocket.settimeout(delay)
##        try:
##            while True:
##                data = self.rsocket.recv(size)
##
##                ip_packet = self.ip.unpack_ip_packet(data)
##                if ip_packet.ip_daddr != self.source_ip or ip_packet.ip_check != 0 or ip_packet.ip_saddr != self.destination_ip:
##                    continue
##
##                tcp_seg = self.unpack_tcp_segment(ip_packet.data)
##                if tcp_seg.tcp_source != self.destination_port or tcp_seg.tcp_dest != self.local_port or tcp_seg.tcp_check != 0:
##                    continue
##                return tcp_seg
##        except socket.timeout:
##            return None

    def _recv(self, size=65535, delay=60):
        """
        Receive data from next layer
        """
        start = time.time()
        while time.time() - start < 60:
            ip_packet_data = self.ip.recv(size, delay)
            if not ip_packet_data:
                continue
            tcp_seg = self.unpack_tcp_segment(ip_packet_data)
            if tcp_seg.tcp_source != self.destination_port or tcp_seg.tcp_dest != self.local_port or tcp_seg.tcp_check != 0:
                continue
            return tcp_seg
        return None

    def recv(self):
        """
        Receive all the data from the next layer
        """
        received_segments = {}

        while True:
            tcp_seg = self._recv()
            if not tcp_seg:
                self.initiates_close_connection()
                sys.exit(1)

            if tcp_seg.tcp_flags & ACK and tcp_seg.tcp_seq not in received_segments:
                received_segments[tcp_seg.tcp_seq] = tcp_seg.data
                self.tcp_ack_seq = tcp_seg.tcp_seq + len(tcp_seg.data)
                # Server wants to close connection
                if tcp_seg.tcp_flags & FIN:
                    self.reply_close_connection()
                    # Transmission is done. Server closes the connection.
                    break
                # If server need to continue to receive
                else:
                    self._send(flags=ACK)

        # Combind list of data into whole piece of data
        sorted_segments = sorted(received_segments.items())
	data = ''.join(v[1] for v in sorted_segments)

        return data

    def recv_ack(self, offset=0):
        start_time = time.time()
        while time.time() - start_time < 60:
            tcp_seg = self._recv(delay=60)
            if not tcp_seg:
                break
            if tcp_seg.tcp_flags & ACK and tcp_seg.tcp_ack_seq >= self.tcp_seq + len(self.send_buf) + offset:
                self.tcp_seq = tcp_seg.tcp_ack_seq
                self.tcp_ack_seq = tcp_seg.tcp_seq + offset
                return True

        return False

    def initiates_close_connection(self):
        """
        Initiates Connection to Close
        """
        self._send(flags=FIN_ACK)
        self.recv_ack(offset=1)

        tcp_seg = self._recv()

        if not (tcp_seg.tcp_flags & FIN):
            print "Close connection failed"
            self.initiates_close_connection()
            sys.exit(1)

        self._send(flags=ACK)
        self.ip.close_all()

    def reply_close_connection(self):
        """
        Close Connections
        """
        self.tcp_ack_seq += 1
        self._send(flags=FIN_ACK)
        tcp_seg = self.recv_ack(offset=1)
        self.ip.close_all()

    def three_way_hand_shake(self):
        """
        Do three way handshake
        """
        self.tcp_seq = randint(0, (2 << 31) - 1)

        self._send(flags=SYN)
        if not self.recv_ack(offset=1):
            print 'connect failed'
            self.initiates_close_connection()
            sys.exit(1)

        self._send(flags=ACK)

    def download(self):
        """
        Download all the data
        """
        self.send(self.http_request)

        data = self.recv()
        if not data.startswith("HTTP/1.1 200 OK"):
            self.initiates_close_connection()
            sys.exit(1)

        return data
