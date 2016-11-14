import socket
request = "GET {url} HTTP/1.0\r\n" + \
          "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n" + \
          "Connection: close\r\n\r\n"

def checksum(msg):
    s = 0
    
    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        if i+1 <= len(msg)-1: 
            w = ord(msg[i]) + (ord(msg[i+1]) << 8 ) 
        else: 
            w = ord(msg[i]) 

        s = s + w
     
    s = (s>>16) + (s & 0xffff);
    s = s + (s >> 16);

    #complement and mask to 4 byte short
    s = ~s & 0xffff
     
    return s

def make_HTTP_GET(url):
    return request.format(url=url)