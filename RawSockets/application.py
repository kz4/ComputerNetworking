from transport import *

class Http(object):
	def __init__(self, source_ip, destination_ip, destination_components, filename):
		self.source_ip = source_ip
		self.destination_ip = destination_ip
		self.destination_components = destination_components
		destination_port = 80
		self.tcp = Tcp(source_ip, destination_ip, destination_components, destination_port)
		self.filename = filename


	def start(self):
		self._create_get_request()
		self.tcp.three_way_hand_shake()
		self.tcp.download(self.filename)
		
	def _create_get_request(self):
		requst = []
		requst.append('GET ' + self.destination_components.path + ' HTTP/1.1\r\n')
		requst.append('Host: ' + self.destination_components.netloc + '\r\n')
		requst.append('\r\n')
		requst_str = ''.join(requst)
		print 'requst_str: ', requst_str

		self.tcp.set_request(requst_str)