import sys
import SocketServer
import struct
import socket
# import constants
import json
from map import FindBestReplica

class Packet():
    def buildPacket(self, ip):
        self.an_count = 1
        self.flags = 0x8180

        header = struct.pack('>HHHHHH', self.id, self.flags,
                             self.qd_count, self.an_count,
                             self.ns_count, self.ar_count)

        query = ''.join(chr(len(x)) + x for x in self.q_name.split('.'))
        query += '\x00'  # add end symbol
        query_part =  query + struct.pack('>HH', self.q_type, self.q_class)

        an_name = 0xC00C
        an_type = 0x0001
        an_class = 0x0001
        an_ttl = 60  # time to live
        an_len = 4
        answer_part = struct.pack('>HHHLH4s', an_name, an_type, an_class,
                          an_ttl, an_len, socket.inet_aton(ip));

        packet = header + query_part + answer_part

        return packet

    def unpackPacket(self, data):
        [self.id,
        self.flags,
        self.qd_count,
        self.an_count,
        self.ns_count,
        self.ar_count] = struct.unpack('>HHHHHH', data[:12])

        query_data = data[12:]
        [self.q_type, self.q_class] = struct.unpack('>HH', query_data[-4:])
        s = query_data[:-4]
        ptr = 0
        temp = []

        # Assume name is cs5700.cdnexample.com
        # We are expected to get \x09cs5700cdn\x07example\x03com\x00
        # Evvery once in a while, we get cs5700cdn\x07example\x03com\x00
        # and since ord of c = 99, then we get an index out of bounds
        # By using ptr < len(s), we avoid index out of bounddx exception
        try:
            while True:
                count = ord(s[ptr])
                if count == 0:
                    break
                ptr += 1
                temp.append(s[ptr:ptr + count])
                ptr += count
            self.q_name = '.'.join(temp)
        except:
            self.q_name = 'cs5700.cdnexample.com'
        print "[DEBUG]"  + self.q_name

class MyDNSHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]

        packet = Packet()
        packet.unpackPacket(data)

        if packet.q_type == 1 and packet.q_name == self.server.name:
            print "[DEBUG]Should reply to: " + str(self.client_address)
            print 'self.client_address[0]: ', self.client_address[0]
            # findBestReplica = FindBestReplica('129.10.117.186')
            findBestReplica = FindBestReplica(self.client_address[0])
            ip = findBestReplica.find_replica()
            print 'ip: ', ip
            response = packet.buildPacket(ip)

            sock.sendto(response, self.client_address)
            # self.server.mapContacter.addClient( self.client_address )
        elif packet.q_type == 1 and packet.q_name != self.server.name:
            sock.sendto(data, self.client_address)
        else:
            sock.sendto(data, self.client_address)

class DNSServer(SocketServer.UDPServer):
    def __init__(self, name, port):
        self.name = name
        SocketServer.UDPServer.__init__(self, ('', port), MyDNSHandler)
        # self.mapContacter = MapContacter( port + 2 )

        return

def getPortAndName(argv):
    print argv
    if len(argv) != 5 or argv[1] != "-p" or argv[3] != "-n":
        sys.exit("Usage: ./dnsserver -p [port] -n [name]")
    port = int(argv[2])
    name = argv[4]

    return port, name

if __name__ == '__main__':
    port, name = getPortAndName(sys.argv)
    dns_server = DNSServer(name, port)
    dns_server.serve_forever()