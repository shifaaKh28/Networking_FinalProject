from pydoc import cli
import socket
from typing import Final
import Packets
import math
import time

bufferSize:Final = 1024 * 1024 * 2
portNumber:Final = 8888
class QUICClient:
    def __init__(self):
        """
        Initialize a QUICClient object.
        """
        self.socket = Packets.QUICSocket()# Create a QUIC socket
        self.streams = [] # List to store active streams
        self.timeTaken = [] # List to store time taken to receive the file

    def create_socket(self):
        """
        Create the client socket.
        """
        print("Creating socket...\n")
        self.socket.create_socket()

    def connect(self, host, port):
        """
        Connect to the server.

        Args:
            host (str): The server's hostname or IP address.
            port (int): The server's port number.
        """

        print("Connecting to server...\n")
        
        self.create_socket()# Create the client socket
        self.socket.set_address((host, port))# Set the server address
        dest_id = Packets.generate_random_hex() # Generate a random destination ID
        self.socket.set_dest_cid(dest_id) # Set the destination connection ID
        qlh = Packets.QUICLongHeader(Packets.LONG_HEADER_FLAG,dest_id, '', 1)# Create a QUIC long header
        self.send_packet(qlh) # Send the QUIC long header packet
        print(f"Sent Client Hello\n")

         # Receive response from server
        print("Waiting for Server response...\n")
        #(self.socket.get_sockfd()).settimeout(5)
        data, _ = self.socket.recvfrom(1024)# Receive data from the server
        data = Packets.QUICLongHeader.decode(data)# Decode the received data
        self.socket.set_src_cid(data.dest_cid) # Set the source connection ID
        print(f"Received Server Hello\n")
        

        # Send ack to server
        qlh = Packets.QUICLongHeader(Packets.LONG_HEADER_FLAG, dest_id, data.dest_cid, 2)

    def send_packet(self, packet):
        self.socket.sendto(packet.encode(), self.socket.get_address())

    def receive_packet(self):
        data, _ = self.socket.recvfrom(bufferSize)  # Adjust buffer size accordingly
        decoded_header = Packets.QUICPacket.decode(data)
        return decoded_header

    def handle_response(self):
    
        print("Receiving files...\n")
        # start a timer to calculate the time taken to receive the file
        start = time.time()
        while True:
            packet = self.receive_packet()
            if not self.streams: 
                for frame in packet.protected_payload:
                    self.streams.append({'id': frame.stream_id,'chunkSize': frame.length , 'packetReceived': 0})
                    self.streams[frame.stream_id]['packetReceived'] += frame.length 
            else:
                for frame in packet.protected_payload:
                    self.streams[frame.stream_id]['packetReceived'] += frame.length
            
            # send ACK
            ack_packet = Packets.QUICAck(packet.packet_number, 0)
            self.send_packet(ack_packet)


            self.timeTaken = [0.0] * len(self.streams)
            for frame in packet.protected_payload:    
                if frame.finished == 1:
                    self.timeTaken[frame.stream_id] = time.time() - start
                    

            

            if all(frame.finished == 1 for frame in packet.protected_payload):
                print("All files received.\n")
                break

            
    # Simulate processing response
    # In a real-world scenario, you would handle stream data here
    def run(self):
        """
        Run the client to simulate file transfers through multiple streams.
        """

        # Simulate initiating file transfers through multiple streams
        offset = 0
        frames = []

        #Ask user how many streams they want to simulate
        try:
            streamNumber = int(input("Enter the number of streams you want to simulate: "))
        except KeyboardInterrupt:
            print("Simulation interrupted by user.")
            self.socket.close()
            exit(0)

        for stream_id in range(0, streamNumber):  # Simulate 3 file transfers
            file_data = (f"Request{stream_id}").encode('utf-8')  # Placeholder request 
            frame = Packets.QUICStreamPayload(stream_id, offset + len(file_data), len(file_data),0, file_data)
            frames.append(frame)
            
        # Send packet
        packet = Packets.QUICPacket(0, self.socket.get_dest_cid(), 1, frames)
        print(f"Sending Request to {self.socket.get_address()}\n")
        self.send_packet(packet)

        # Handle response
        self.handle_response()
        self.printStatistics()

    def printStatistics (self):
        print("Printing statistics...\n")

        # part A: number of bytes received in each stream
        print("Number of bytes received in each stream:")
        for stream in self.streams:
            print(f"Stream {stream['id']} received {stream['packetReceived']} bytes")
        print("---------------------------------------------------------------")
        # part B: number of packets received in each stream
        print("Number of packets received in each stream:")
        for stream in self.streams:
            print(f"Stream {stream['id']} received {math.ceil(stream['packetReceived'] / stream['chunkSize'])} packets")
        print("---------------------------------------------------------------")

        # part C: bandwidth of each stream in bytes per second (b/s) and packets per second (pps)
        print("Bandwidth of each stream:")

        for stream in self.streams:
            print(f"Stream {stream['id']} bandwidth: {round (stream['packetReceived'] / self.timeTaken[stream['id']],2)} B/s, { math.ceil(stream['packetReceived'] / stream['chunkSize'] / self.timeTaken[stream['id']])} packets per second")
        print("---------------------------------------------------------------")
        # part D: total bandwidth in bytes per second (B/s)
        total = sum([stream['packetReceived'] for stream in self.streams])
        print(f"Total bandwidth: {round(total / max(self.timeTaken),2)} B/s")
        
        print("---------------------------------------------------------------")
        # part E: total number of packets received
        total_packets = sum([math.ceil(stream['packetReceived'] / stream['chunkSize']) for stream in self.streams])
        print(f"Total packets received: {total_packets} packets per second")

if __name__ == "__main__":
    print("QUIC client started\n")
    client = QUICClient()
    client.connect('127.0.0.1', portNumber)
    client.run()
    client.socket.close()
