from threading import Thread, Lock
import socket
import json
import time
lock = Lock()
import sys

# Original server
replicaIps = ['52.4.98.110']
# Key: client IP, value: (ping time, replica IP, last request time)
clientIpMap = {}


class Map(object):
	def __init__(self, port):
		self.getPingTime()
		self.port = port
		self.threads = []
		self.initThreads()

	def initThreads(self):
		for ip in replicaIps:
			thread = replicaThread(ip, self.port)
			thread.daemon = True
			self.threads.append(thread)
			thread.start()

class replicaThread(Thread):
	def __init__(self, ip, port):
		Thread.__init__(self)
		self.ip = ip
		# Socket used to communicate client IP with Ping Server (pingServer.py)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.port = port
		self.sock.settimeout(1)

	def run(self):
		while True:
			lock.acquire()
			for clientIp in clientIpMap:
				# 600 seconds
				if time.time() - clientIpMap[clientIp][2] > 600:
					clientIpMap.pop(clientIp)
			lock.release()
			try:
				clientIpTimeSpanJson = json.dumps({'PingRequest': \
										{'ClientIps' : clientIpMap.keys(), \
										'TimeSpan' : time.time(), 'ReplicaIp' : self.ip}})
				self.sock.sendto(clientIpTimeSpanJson, (self.ip, self.port))

				resJson, replicaIp = self.sock.recvfrom(1024)
				if replicaIp == self.ip:
					res = json.loads(resJson)
					if res.has_key('PingResult'):
						pingTimeDict = res['PingResult']['PingTimeDict']
						lock.acquire()
						for clientIp in pingTimeDict:
							# If client IPs are not active for some time, we remove them from
							if clientIp in clientIpMap and clientIpMap[clientIp][0] > pingTimeDict[clientIp]:
								lastTime = clientIpMap[clientIp][2]
								clientIpMap[clientIp] = (pingTimeDict[clientIp], self.ip, lastTime)
						lock.release()
			except:
				pass
			time.sleep(1)

if __name__ == '__main__':
	map = Map(sys.argv[1])