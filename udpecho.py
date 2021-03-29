#! /usr/bin/env python3

# Client and server for udp (datagram) echo.
#
# Usage: udpecho -s      (to start a server)
# or:    udpecho -c host (to start a client)

# Reference :
# http://svn.python.org/projects/python/trunk/Demo/sockets/udpecho.py

import socket
import struct
import sys
import time
import numpy
from dataclasses import dataclass

PORT = 10000
BUFSIZE = 1024

# Message format
# 1 byte : Code (0 = Done, 1 = OK )
# 1 long int : Sequence number
# 1 long int : Timestamp
# 448 bytes : padding
# Total : 472 bytes of data
# Packet size : 20 bytes IP + 8 bytes UDP + 472 bytes data = 500 bytes
message = struct.Struct( 'B Q Q 448x' )
message_done = struct.pack( 'B', 0 )
message_ok = struct.pack( 'B', 1 )

def main():
	if len(sys.argv) < 2 : usage()
	if sys.argv[1] == '-s' : server()
	elif sys.argv[1] == '-c' : client()
	else : usage()

def usage():
	sys.stdout = sys.stderr
	print( 'Usage: udpecho -s      (to start a server)' )
	print( 'or:    udpecho -c host (to start a client)' )
	sys.exit( 2 )

def server():
	s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	s.bind( ( '', PORT ) )
	print( 'udp echo server ready' )
	arrival_time = []
	while True :
		data, addr = s.recvfrom( BUFSIZE )
		arrival_time.append( time.perf_counter_ns() )
		s.sendto( message_ok, addr )
		if not data[0] : break
	data, addr = s.recvfrom( BUFSIZE )
	latency_min, latency_max, latency_mean = struct.unpack( 'd d d', data )
	s.close()
	print( 'Latency : min = {:.3f}ms - max = {:.3f}ms - mean = {:.3f}ms'.format( latency_min, latency_max, latency_mean ) )
	jitter = numpy.abs( numpy.diff( arrival_time, 2 ) ) / 1000000
	print( 'Jitter :  min = {:.3f}ms - max = {:.3f}ms - mean = {:.3f}ms'.format( numpy.min(jitter), numpy.max(jitter), numpy.mean(jitter) ) )


def client():
	if len(sys.argv) < 3 : usage()
	host = sys.argv[2]
	addr = host, PORT
	s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	s.bind( ( '', 0 ) )
	print( 'udp echo client ready' )
	i = 0
	latency = []
	while i < 10 :
		t1 = time.perf_counter_ns()
		s.sendto( message.pack( 1, i, t1 ), addr )
		data, fromaddr = s.recvfrom( BUFSIZE )
		t2 = time.perf_counter_ns()
		latency.append( t2 - t1 )
		# One message every 200ms
		time.sleep( 0.2 )
		i += 1
	s.sendto( message_done, addr )
	latency = numpy.asarray( latency ) / 1000000
	s.sendto( struct.pack( 'd d d', numpy.min(latency), numpy.max(latency), numpy.mean(latency) ), addr )
	s.close()
	print( 'Latency : min = {:.3f}ms, max = {:.3f}ms, mean = {:.3f}ms'.format( numpy.min(latency), numpy.max(latency), numpy.mean(latency) ) )


main()
