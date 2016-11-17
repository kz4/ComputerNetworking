# Warning:
1. The network interface on our machine is ```eno16777736```, but I noticed most of other network interface is ```eth0```, please change accordingly. Use ifconfig to see all your network interface names
2. In datalink.py line 191,
```return mac_addresses[1].replace(":", "")```
in my case, eno16777736 is the second MAC address in the array, change accordingly

# Run these three lines first:
 ```
 sudo ethtool --offload [network interface name] rx off tx off
 sudo ethtool -K [network interface name] gso off
 sudo ethtool -K [network interface name] gro off
 ```

# High Level Approach:
In this project, the goal is to implement low-level operations of the Internet protocol stack with our own OSI model,
 which includes Application Layer, Transport Layer and Network Layer. The program is run by
```sudo ./rawhttpget [url]```
and the url will be downloaded using the raw socket we created.

The program starts from the main file, and then propagates to the Application Layer, which calls the TCP Layer, which
 in turn calls the IP Layer. After we get all the packet on the IP layer, we return it in the opposite order of how it
 first propagates down.

The following figure shows the layer structure and all functions implemented in each layer:
```
=====================================
| .       /rawhttpget url           |
=====================================
             ^
             | (api)
Http:                    => HTTP get request, parse the url,
download                   remove header, remove chuck length, save files

=====================================
|application(application.py) Http(String)  |
=====================================
             ^
             | (api)
Tcp:    	          => three way handshake, send tcp packet, receive tcp packet
send, recv, connect,    time out, congestion control, out-order packet dealing
close                       retransmission, TCP packet checksum validation

=====================================
|transport(transport.py) TcpPacket  |
=====================================
             ^
             | (api)
Ip:                => send ip packet, receive ip packet, filter the packet by
send, recv                  packet type, IP packet checksum validation
close

=====================================
|network(network.py)     IpPacket   |
=====================================
             ^
             | (api)
Datalink:          => ARP the gateway MAC address by its ip, send ethernet packet,
send, recv                  receive ethernet packet

=====================================
|datalink(datalink.py)   EtherPacket|
=====================================
             ^
             | (api)


AF_PACKET, RAW_SOCK      => basic data sending and receiving
sendto, recvfrom

=====================================
|             OS(linux)	         |
=====================================
```

# Features Implemented:
TCP:
We implemented the TCP pack header, checksum of incoming TCP segments and generate correct checksums for outgoing
 segments. Perform the three-way handshake before sending the HTTP GET request and deal with the connection teardown.
 Sort out-of-order segments in the correct order and discard duplicate segments

IP:
We implemented the IP pack header, and all features of IP packets, including validating the checksum of
 incoming/outgoing packets, setting correct version, header length, total length and protocol identifier. And we query
 the IP of remote HTTP server and source machine to set the source and destination IP in outgoing packet. And we
 implemented validity check of IP headers, checksum and protocol identifier

Datalink:
We implemented the Data Link Layer by wrapping the two raw sockets, one for send and one for receive. For the send part,
 we build the connection first, then we get the Gateway IP and MAC address by ARP. Then we use the IP packet to assemble
 an Ethernet frame and send out. For the receive part, we use a loop to fetch Ethernet frames from the raw socket, and
 then we disassemble the frame. If the destination MAC addresses and source MAC addresses match, then we return the
 data part

# Challenges:
1. Understand the overall flow, design an architecture so that data can flow freely between different layers
2. Understand how to pack/unpack the struct is not easy. This includes how header fields are shifted, how characters
 are formatted and etc. Made many mistakes along the way
3. Learn how to set up WireShark, set filters and where to look for packets
4. When downloading a web page, in the beginning, we did not realize the chunk length needs to be removed and thought
 we had some logic error in the code. Then we figured out, instead of writing the whole file out, we should read each
 part up to the chuck length and keeps repeating
5. When calculating the check sum, initially, we didn't have the pseudo-header, so the check sum logic was not correct
6. There might be option fields in TCP and IP headers. We have to discover them and remove them
7. The checksum of TCP during recv is not correct. It turned out to be the TCP checksum offloading. We fixed it by running
```
 sudo ethtool --offload [network interface name] rx off tx off
 sudo ethtool -K [network interface name] gso off
 sudo ethtool -K [network interface name] gro off
```
8. Have to get the data link protocol exactly right during Ethernet frame assembling
