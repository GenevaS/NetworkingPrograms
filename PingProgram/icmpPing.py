# ----------------------------------------------------------------
# Geneva Smith
# ICMP Pinger
# ----------------------------------------------------------------
# This program allows users to send ICMP packets to a remote host
# to determine if it can be reached through the network.
# ----------------------------------------------------------------
import socket
import os
import sys
import platform
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

# ----------------------------------------------------------------
# Function: checksum
# ----------------------------------------------------------------
# Function determines the validity of the checksum in a
# packet header.
# Used in the sendOnePing function
# ----------------------------------------------------------------
def checksum(str):
    csum = 0
    countTo = (len(str) / 2) * 2

    count = 0
    while count < countTo:
        thisVal = ord(str[count+1]) * 256 + ord(str[count])
        csum = csum + thisVal
        csum = csum & 0xffffffffL
        count = count + 2

    if countTo < len(str):
        csum = csum + ord(str[len(str) - 1])
        csum = csum & 0xffffffffL

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    
    return answer

# ----------------------------------------------------------------
# Function: receiveOnePing
# ----------------------------------------------------------------
# Function receives an ICMP packet from the server-side
# host. Returns -1 if the requested timed out.
# Used in the doOnePing function
# ----------------------------------------------------------------
def receiveOnePing(icmpSocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([icmpSocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)

        # Timeout
        if whatReady[0] == []:
            print "Request timed out."
            return -1

        # Determine time of receipt and get the packet and its
        # address of origin
        timeReceived = time.time()
        recPacket, addr = icmpSocket.recvfrom(1024)

        # Fetch the IP packet header
        # ipVer = Version, IHL
        # servType = Services
        # length = Total length
        # ipID = ID
        # ipFlagsOff = Flags, Fragment Offset
        # ipTTL = Time to Live
        # ipProc = Protocol
        # ipChecksum = checksum
        # ipSrc = Source IP address
        # ipDest = Destination IP address
        ipHeader = recPacket[:20]
        ipVer, servType, length, ipID, ipFlagsOff, ipTTL, ipProc, ipChecksum, ipSrc, ipDest = struct.unpack("BBHHHBBHII", ipHeader)
        
        # Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]
        icmpType, code, checksum, packID, sequence = struct.unpack("bbHHh", icmpHeader)
        if packID == ID:
            timeSent = struct.unpack("d", recPacket[28:28 + struct.calcsize("d")])[0]
            
            # Print out reply information
            delayMS = (timeReceived - timeSent)*1000
            packetSize = len(recPacket)
            if (delayMS < 1):
                print "Reply from " + destAddr + ": bytes=" + str(packetSize) + " time<=1ms TTL=" + str(ipTTL)
            else:
                print "Reply from " + destAddr + ": bytes=" + str(packetSize) + " time=" + str(int(round(delayMS,1))) + "ms TTL=" + str(ipTTL)
                
            return delayMS
        
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            print "Request timed out."
            return -1

# ----------------------------------------------------------------
# Function: sendOnePing
# ----------------------------------------------------------------
# Function sends an ICMP packet to a server-side host
# to determine if the remote host can be reached.
# * Header is type (8), code (8), checksum (16), id (16),
#   sequence (16)
# * struct -- Interpret strings as packed binary data
# * AF_INET address must be tuple, not str
# * Both LISTS and TUPLES consist of a number of objects which can
#   be referenced by their position number within the object
# Used in the doOnePing function
# ----------------------------------------------------------------
def sendOnePing(icmpSocket, destAddr, ID, pingnum):   
    srcChecksum = 0
    
    # Make a dummy header with a 0 checksum.
    # bbHHh = signed char, signed char, unsigned short, unsigned short, short
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, srcChecksum, ID, 1)
    # d = double
    data = struct.pack("d", time.time())
    
    # Calculate the checksum on the data and the dummy header.
    srcChecksum = checksum(header + data)
    
    # Calculate the checksum for the packet
    if sys.platform == 'darwin': # Mac OS X
        #Convert 16-bit integers from host to network byte order.
        srcChecksum = socket.htons(srcChecksum) & 0xffff
    else: # Linux, UNIX, Windows
        srcChecksum = socket.htons(srcChecksum)

    # Fill in header checksum with correct value
    # bbHHh = signed char, signed char, unsigned short, unsigned short, short
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, srcChecksum, ID, 1)
    packet = header + data

    if (pingnum == 0):
        packetSize = len(packet)
        headerSize = len(header)
        dataSize = len(data)
        print "Pinging " + destAddr + " with " + str(packetSize) + " bytes of data (Header=" + str(headerSize) + " bytes, Data=" + str(dataSize) + " bytes)"
        print ""
        
    icmpSocket.sendto(packet, (destAddr, 1)) 

# ----------------------------------------------------------------
# Function: doOnePing
# ----------------------------------------------------------------
# Function does a complete ping-pong relay with a
# remote host.
# * SOCK_RAW is a powerful socket type.
# * For more details see: http://sock-raw.org/papers/sock_raw
# Used in the ping function
# ----------------------------------------------------------------
def doOnePing(destAddr, timeout, pingnum):
    #Create Raw Socke
    icmp = socket.getprotobyname("icmp")
    icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    #Return the current process i
    procID = os.getpid() & 0xFFFF

    # Do a ping-pong relay with the remote host
    sendOnePing(icmpSocket, destAddr, procID, pingnum)
    delay = receiveOnePing(icmpSocket, procID, timeout, destAddr)

    # Close socket and return result
    icmpSocket.close()
    return delay

# ----------------------------------------------------------------
# Function: ping
# ----------------------------------------------------------------
# Function prepares and initiates a ping-pong relay with
# a remote hosts and reports the result.
# * timeout=1 means: If one second goes by without a reply from 
#   the server, the client assumes that either the client's ping 
#   or the server's pong is lost. This is an optional argument -
#   if a value is provided in the calling function, the value will
#   be 1
# Main function
# ----------------------------------------------------------------
def ping(host, timeout=1, pings=4):
    delay = []
    minRTT = 1000000
    maxRTT = -1
    sumRTT = 0
    lost = 0
    
    # Get name of remote host
    dest = socket.gethostbyname(host)

    pythonVersion = platform.python_version()
    print ""
    print "Python " + pythonVersion + " pinging " + host
    print ""

    #Send ping requests to a server separated by <timeout> second
    for i in range(0, pings):
        delay.append(doOnePing(dest, timeout, i))
        time.sleep(1)

    # Calculate ping statistics
    for i in range(0, pings):
        if (delay[i] == -1):
            lost = lost + 1
        else:
            if (delay[i] < minRTT):
                minRTT = delay[i]
            if (delay[i] > maxRTT):
                maxRTT = delay[i]
            sumRTT = sumRTT + delay[i]

    lostPercent = (float(lost) / pings) * 100
    receivedPings = pings - lost
    averageRTT = sumRTT / pings

    print ""
    print "Packet statistics for " + dest + ":"
    print "\tSent = " + str(pings) + " Received = " + str(receivedPings) + " Lost = " + str(lost) + " (" + str(lostPercent) + "% loss)"
    if (lostPercent < 100):
        print "Approximate round trip times (RTT) in milliseconds:"
        print "\tMinimum=" + str(round(minRTT, 1)) + "ms Maximum=" + str(round(maxRTT, 1)) + "ms Average=" + str(round(averageRTT, 1)) + "ms"

# ----------------------------------------------------------------
# ----------------------------------------------------------------
# Run a test to see if the ping program works as expected
# ----------------------------------------------------------------
# ----------------------------------------------------------------
ping("127.0.0.1")
print ""
print ""
ping("www.google.ca")
print ""
print ""
ping("www.google.ca",1,2)
print ""
print ""
ping("www.poly.edu")
