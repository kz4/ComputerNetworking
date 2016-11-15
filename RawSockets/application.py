from transport import *
import re

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

        self.tcp.set_request(requst_str)

    def _remove_header(self, data):
        """ Sample Header
        HTTP/1.1 200 OK
        Date: Mon, 14 Nov 2016 22:48:33 GMT
        Server: Apache/2.4.18 (Unix) OpenSSL/1.0.1e-fips mod_bwlimited/1.4 mod_fcgid/2.3.9
        X-Powered-By: PHP/5.6.21
        Keep-Alive: timeout=5, max=100
        Connection: Keep-Alive
        Transfer-Encoding: chunked
        Content-Type: text/html; charset=UTF-8
        """

        """ Header is followed by a \r\n\r\n, which is then followed by a chunk length, chunk
        Header

        172b
        ...
        ...
        3b04
        ...
        ...
        0


        """
        content = data.split("\r\n\r\n", 1)
        return content[1]

    def _remove_chunk_length(self, data):
        content = []
        while True:
            # Get the chunk length and rest of data respectively
            first_line = data.split('\r\n', 1)[0]
            rest_data = data.split('\r\n', 1)[1]
            m = re.match(r'^[a-zA-Z0-9]+$', first_line)
            # Find chunk, and read data according to the chunk length
            if m is not None:
                chunk_size = int(m.group(0), 16)
                content.append(rest_data[:chunk_size])
                data = rest_data[chunk_size + 2:]
                # If chuck is 0, exit out of the while loop, which means we have received all the data
                if chunk_size == 0:
                    break
            # If can not find chunk, raise exception
            elif m is None:
                return data

        return ''.join(content)