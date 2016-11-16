import argparse
import sys
import socket
import struct
import time
import socket

from random import randint
from collections import namedtuple, OrderedDict
from util import checksum

IP_HDR_FMT = '!BBHHHBBH4s4s'
IPDatagram = namedtuple(
    'IPDatagram', 'ip_tlen ip_id ip_frag_off ip_saddr ip_daddr data ip_check')

class Ip(object):
    def __init__(self, local_host, remote_host):
        self.local_host = local_host
        self.remote_host = remote_host       
        self.ssocket = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                     socket.IPPROTO_RAW)
        self.rsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                     socket.IPPROTO_TCP)

    def pack_ip_packet(self, payload):
        '''
        Generate IP datagram.
        `payload` is TCP segment
        '''
        ip_tos = 0
        ip_tot_len = 20 + len(payload)
        ip_id = randint(0, 65535)
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0
        ip_saddr = socket.inet_aton(self.local_host)
        ip_daddr = socket.inet_aton(self.remote_host)

        ip_ihl_ver = (4 << 4) + 5
        ip_header = struct.pack(IP_HDR_FMT, ip_ihl_ver, ip_tos, ip_tot_len,
                                ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
        ip_check = checksum(ip_header)

        ip_header = struct.pack(IP_HDR_FMT, ip_ihl_ver, ip_tos, ip_tot_len,
                                ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)

        return ip_header + payload


    def unpack_ip_packet(self, datagram):
        '''
        Parse IP datagram
        '''
        hdr_fields = struct.unpack(IP_HDR_FMT, datagram[:20])
        ip_header_size = struct.calcsize(IP_HDR_FMT)
        ip_ver_ihl = hdr_fields[0]
        ip_ihl = ip_ver_ihl - (4 << 4)

        if ip_ihl > 5:
            opts_size = (ip_ihl - 5) * 4
            ip_header_size += opts_size

        ip_headers = datagram[:ip_header_size]

        data = datagram[ip_header_size:hdr_fields[2]]
        ip_check = checksum(ip_headers)

        return IPDatagram(ip_daddr=socket.inet_ntoa(hdr_fields[-1]),
            ip_saddr=socket.inet_ntoa(hdr_fields[-2]),
            ip_frag_off=hdr_fields[4],
            ip_id=hdr_fields[3], 
            ip_tlen=hdr_fields[2], 
            ip_check=ip_check, data=data)

    def send(self, tcp_segment, destination_info):
        ip_packet = self.pack_ip_packet(tcp_segment)
        self.ssocket.sendto(ip_packet, destination_info)

    def recv(self, size, delay):
        self.rsocket.settimeout(delay)
        try:
            while True:
                data = self.rsocket.recv(size)

                ip_packet = self.unpack_ip_packet(data)
                if ip_packet.ip_daddr != self.local_host or ip_packet.ip_check != 0 or ip_packet.ip_saddr != self.remote_host:
                    continue
                return ip_packet.data
        except socket.timeout:
            return None       

    def close_all(self):
        self.ssocket.close()
        self.rsocket.close()