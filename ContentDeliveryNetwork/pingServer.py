import socket
import json

class PingServer(object):
    def __init__(self, port):
        # Socket used to communicate RTT with Map (map.py)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = port
        # self.sock.settimeout(1)
        # TODO: Change 52.4.98.110 (EC2 IP) to server's own IP
        # self.ip = '54.210.1.206'
        # self.ip = '129.10.106.91'
        # self.ip = '54.167.4.20' #original EC2
        # self.ip = '129.10.117.186' # cs5700cdnproject.ccs.neu.edu
        self.ip = '' # cs5700cdnproject.ccs.neu.edu

        self.sock.bind((self.ip, port))

    def run(self):
        while True:
            # clientIpTimeSpanJson = json.dumps({'PingRequest': \
            #                           {'ClientIps' : clientIpMap.keys(), \
            #                           'TimeSpan' : time.time(), 'ReplicaIp' : self.ip}})
            reqJson, replicaIp = self.sock.recvfrom(1024)
            print 'reqJson, replicaIp: ', reqJson, replicaIp
            res = json.loads(resJson)
            if res.has_key('PingRequest') and res['PingRequest']['ReplicaIp'] == self.ip:
                clientIps = res['PingRequest']['ClientIps']
                resultDict = {}
                for clientIp in clientIps:
                    rtt = getPingTime(clientIp)
                    print 'clientIp: ', clientIp
                    print 'rtt: ', rtt
                    if rtt:
                        resultDict[clientIp] = rtt
                self.sendPingResult(resultDict)

    def sendPingResult(self, resultDict):
        resultJson = json.dumps({'PingResult' : {'PingTimeDict' : resultDict}})
        self.sock.sendto(resultJson, (self.ip, self.port))
        print 'finish sending in PingServer'

    def getPingTime(self, clientIp):
        command = "scamper -c 'ping -c 1' -i " + clientIp + " | grep 'time='"
        outputs = os.popen(command).read()
        print outputs
        if outputs.find('time='):
            m = re.search('time=([0-9]*.[0-9]*)', outputs)
            if m:
                return float(m.group(1))
        return None

if __name__ == '__main__':
    pingServer = PingServer(55555)
    pingServer.run()