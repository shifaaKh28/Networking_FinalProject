import socket  # Importing the socket module for network communication
import sys  # Importing the sys module for system-specific parameters and functions
from typing import Final  # Importing Final from typing for defining constants
import Packets  # Importing the Packets module which contains various QUIC-related classes
import os  # Importing the os module for generating random data
import random  # Importing the random module for random number generation
import math  # Importing the math module for mathematical operations

# Defining constants
portNumber: Final = 8888  # Port number for the server
oneMB: Final = 1024 * 1024  # Size of 1 MB in bytes
fiveMB: Final = 5 * oneMB  # Size of 5 MB in bytes
minNumberOfBytes: Final = 1000  # Minimum number of bytes for a chunk
maxNumberOfBytes: Final = 2000  # Maximum number of bytes for a chunk

class QUICServer:
    def __init__(self, host='127.0.0.1', port=portNumber):
        """
        Initialize a QUICServer object.

        Args:
            host (str): Host address of the server.
            port (int): Port number of the server.
        """
        self.host = host
        self.port = port
        self.socket = Packets.QUICSocket()
        self.streams = []  # List to store active streams
        self.i = 0

    def create_socket(self):
        """
        Create and bind the server socket.
        """
        print("Creating socket...\n")
        self.socket.create_socket()
        self.socket.bind((self.host, self.port))

    def accept(self):
        """
        Accept a connection from a client and perform the initial handshake.
        """
        self.create_socket()
        print("Accepting connection...\n")
        data, address = self.socket.recvfrom(1024)  # Receive data from a client
        self.socket.set_address(address)
        data = Packets.QUICLongHeader.decode(data)  # Decode the received data
        self.socket.set_src_cid(data.dest_cid)
        dest_conn_id = Packets.generate_random_hex()
        self.socket.set_dest_cid(dest_conn_id)
        print(f"Received Client Hello from {address}")
        qlh = Packets.QUICLongHeader(Packets.LONG_HEADER_FLAG, dest_conn_id, data.dest_cid, data.packet_number)
        self.socket.sendto(qlh.encode(), address)  # Send server hello to the client
        print(f"Sent Server Hello to {address}")

    def send_packet(self, packet, address):
        """
        Send a packet to a specified address.

        Args:
            packet (Packets.QUICPacket): The packet to send.
            address (tuple): The address to send the packet to.
        """
        self.socket.sendto(packet.encode(), address)

    def receive_packet(self):
        """
        Receive a packet from the client.

        Returns:
            Packets.QUICPacket: The received packet.
        """
        data, _ = self.socket.recvfrom(1024)  # Adjust buffer size accordingly
        decoded_header = Packets.QUICPacket.decode(data)
        if not isinstance(decoded_header, Packets.QUICPacket):
            print("Invalid packet received. Exiting...")
            self.socket.close()
            exit(1)
        return decoded_header
    
    def receive_ack(self):
        """
        Receive an ACK packet from the client.

        Returns:
            Packets.QUICAck: The received ACK packet.
        """
        data, _ = self.socket.recvfrom(1024)
        decoded_header = Packets.QUICAck.decode(data)
        if not isinstance(decoded_header, Packets.QUICAck):
            print("Invalid ACK packet received. Exiting...")
            self.socket.close()
            exit(1)
        return decoded_header

    def handle_client(self):
        """
        Handle the client connection and process data streams.
        """
        self.socket.get_sockfd().settimeout(None)
        packet = self.receive_packet()
        self.socket.get_sockfd().settimeout(3)
        if packet.flags == 0:  # Check if stream exists
            for frame in packet.protected_payload:
                if frame.stream_id not in self.streams:
                    self.streams.append({'id': frame.stream_id, 'data': b'', 'totalSent': 0})
        
        streamNumber = len(packet.protected_payload)
        print(f"Received request for {streamNumber} streams\n")
        self.generate_random_data(streamNumber)
        self.send_data(streamNumber)
    
    def generate_random_data(self, stream_number):
        """
        Generate random data for the streams.

        Args:
            stream_number (int): Number of streams to generate data for.
        """
        for i in range(stream_number):
            data = os.urandom(random.randint(oneMB, fiveMB))  # Generate 1 MB - 5 MB of random data
            self.streams[i]['data'] = data

    def send_data(self, streamNumber):
        """
        Divide data into chunks and send it via streams.

        Args:
            streamNumber (int): Number of streams to send data to.
        """
        print("Sending files...\n")
        for i in range(streamNumber):
            r = random.randint(minNumberOfBytes, maxNumberOfBytes)  # Generate random chunk size between 1000 and 2000 bytes
            self.streams[i]['chunkSize'] = r

        max_packets = -sys.maxsize - 1
        for stream in self.streams:
            max = math.ceil(len(stream['data']) / stream['chunkSize'])
            if max > max_packets:
                max_packets = max
            
        for i in range(max_packets):
            frames = []
            for j in range(streamNumber):
                offset = self.streams[j]['chunkSize'] * i
                if offset + self.streams[j]['chunkSize'] >= len(self.streams[j]['data']):
                    remaining = len(self.streams[j]['data']) - offset
                else:
                    remaining = self.streams[j]['chunkSize']

                data = self.streams[j]['data'][offset:offset + remaining]
                self.streams[j]['totalSent'] += len(data)
                totalSent = self.streams[j]['totalSent']
                if offset + remaining >= len(self.streams[j]['data']):
                    finished = 1
                else:
                    finished = 0
                streamPayload = Packets.QUICStreamPayload(stream_id=j, offset=totalSent, finished=finished, length=len(data), stream_data=data)
                frames.append(streamPayload)
            packet = Packets.QUICPacket(0, self.socket.get_dest_cid(), i, frames)
            
            self.send_packet(packet, self.socket.get_address())
            self.receive_ack()  # Receive ACK for the packet
            
        print("Files sent.\n")

if __name__ == "__main__":
    print("Server Running")
    server = QUICServer()  # Create a QUIC server instance
    server.accept()  # Accept a connection from the client
    server.handle_client()  # Handle the client
    server.socket.close()  # Close the socket
