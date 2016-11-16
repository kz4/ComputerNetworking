import socket
import array

def checksum(s):
    if len(s) & 1:
    	s = s + '\0'
    words = array.array('h', s)
    sum = 0
    for word in words:
    	sum = sum + (word & 0xffff)
    hi = sum >> 16
    lo = sum & 0xffff
    sum = hi + lo
    sum = sum + (sum >> 16)
    return (~sum) & 0xffff