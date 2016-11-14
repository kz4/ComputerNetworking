from transport import *

class Http(object):
    def __init__(self, source_ip, destination_ip, destination_components):
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.destination_components = destination_components
        destination_port = 80
        self.tcp = Tcp(source_ip, destination_ip, destination_components, destination_port)

    def start(self):
        self._create_get_request()
        self.tcp.three_way_hand_shake()
        whole_file = self.tcp.download()
        without_header = self._remove_header(whole_file)
        updated_file = self._remove_chunk_length(without_header)
        return updated_file
        
    def _create_get_request(self):
        requst = []
        requst.append('GET ' + self.destination_components.path + ' HTTP/1.1\r\n')
        requst.append('Host: ' + self.destination_components.netloc + '\r\n')
        requst.append('Connection: keep-alive\r\n')
        requst.append('\r\n')
        requst_str = ''.join(requst)
        print 'requst_str: ', requst_str

        self.tcp.set_request(requst_str)

    def _remove_header(self, data):
        pos = data.find("\r\n\r\n")
        if pos > -1:
            pos += 4
            data = data[pos:]
        
        return data

    def _remove_chunk_length(self, data):
        pass