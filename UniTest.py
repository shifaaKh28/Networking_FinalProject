import unittest  # Importing the unittest module for creating unit tests
from Packets import *  # Importing all classes and functions from the Packets module
from Client import QUICClient  # Importing the QUICClient class from the Client module
from Server import QUICServer  # Importing the QUICServer class from the Server module
import threading  # Importing the threading module for creating separate threads
import time  # Importing the time module for time-related functions

class TestQUICPacket(unittest.TestCase):
    def test_packet_encoding_decoding(self):
        """
        Test encoding and decoding of QUICPacket.
        """
        # Create a sample QUIC packet
        flags = 1
        dest_conn_id = "1234567890abcdef"
        packet_number = 1
        payload = [{'stream_id': 0, 'offset': 0, 'finished': 0, 'length': 10, 'stream_data': b'hello'}]
        quic_packet = QUICPacket(flags, dest_conn_id, packet_number, payload)

        # Encode the packet
        encoded_packet = quic_packet.encode()

        # Decode the encoded packet
        decoded_packet = QUICPacket.decode(encoded_packet)

        # Check if the decoded packet matches the original packet
        self.assertEqual(quic_packet.flags, decoded_packet.flags)
        self.assertEqual(quic_packet.dest_conn_id, decoded_packet.dest_conn_id)
        self.assertEqual(quic_packet.packet_number, decoded_packet.packet_number)
        self.assertEqual(quic_packet.protected_payload, decoded_packet.protected_payload)

class TestQUICLongHeader(unittest.TestCase):
    def test_long_header_encoding_decoding(self):
        """
        Test encoding and decoding of QUICLongHeader.
        """
        # Create a sample QUIC long header
        flags = 1
        dest_conn_id = "1234567890abcdef"
        src_conn_id = "abcdef1234567890"
        packet_number = 1
        quic_long_header = QUICLongHeader(flags, dest_conn_id, src_conn_id, packet_number)

        # Encode the long header
        encoded_long_header = quic_long_header.encode()

        # Decode the encoded long header
        decoded_long_header = QUICLongHeader.decode(encoded_long_header)

        # Check if the decoded long header matches the original long header
        self.assertEqual(quic_long_header.flags, decoded_long_header.flags)
        self.assertEqual(quic_long_header.dest_cid, decoded_long_header.dest_cid)
        self.assertEqual(quic_long_header.src_cid, decoded_long_header.src_cid)
        self.assertEqual(quic_long_header.packet_number, decoded_long_header.packet_number)

class TestQUICSocket(unittest.TestCase):
    def test_socket_functionality(self):
        """
        Test the functionality of QUICSocket.
        """
        # Create a QUIC socket
        quic_socket = QUICSocket()
        quic_socket.create_socket()

        # Set address and connection IDs
        address = ('127.0.0.1', 8888)
        dest_cid = "1234567890abcdef"
        src_cid = "abcdef1234567890"

        quic_socket.set_address(address)
        quic_socket.set_dest_cid(dest_cid)
        quic_socket.set_src_cid(src_cid)

        # Check if the address and connection IDs are set correctly
        self.assertEqual(quic_socket.get_address(), address)
        self.assertEqual(quic_socket.get_dest_cid(), dest_cid)
        self.assertEqual(quic_socket.get_src_cid(), src_cid)

        # Check if the socket is created successfully
        self.assertIsNotNone(quic_socket.get_sockfd())

        # Close the socket
        quic_socket.close()

class TestQUICStreamPayload(unittest.TestCase):
    def test_stream_payload_handling(self):
        """
        Test the handling of QUICStreamPayload.
        """
        # Create a sample stream payload
        stream_id = 0
        offset = 0
        length = 10
        finished = 0
        stream_data = b'hello'
        stream_payload = QUICStreamPayload(stream_id, offset, length, finished, stream_data)

        # Encode the stream payload
        encoded_payload = stream_payload.encode()

        # Decode the encoded payload
        decoded_payload = QUICStreamPayload.decode(encoded_payload)

        # Check if the decoded payload matches the original payload
        self.assertEqual(stream_payload.stream_id, decoded_payload.stream_id)
        self.assertEqual(stream_payload.offset, decoded_payload.offset)
        self.assertEqual(stream_payload.length, decoded_payload.length)
        self.assertEqual(stream_payload.finished, decoded_payload.finished)
        self.assertEqual(stream_payload.stream_data, decoded_payload.stream_data)

class TestClientServerInteraction(unittest.TestCase):
    def test_client_server_interaction(self):
        """
        Test the interaction between QUIC client and server.
        """
        # Start the QUIC server in a separate thread
        server_thread = threading.Thread(target=self.start_server)
        server_thread.start()
        time.sleep(2)  # Wait for the server to start

        # Create a QUIC client
        client = QUICClient()

        # Connect to the server
        client.connect('127.0.0.1', 8888)

        # Run the client
        client.run()

        # Close the server and client sockets
        self.server.socket.close()
        client.socket.close()

    def start_server(self):
        """
        Start the QUIC server.
        """
        # Create and start the QUIC server
        self.server = QUICServer()
        self.server.accept()
        self.server.handle_client()

if __name__ == '__main__':
    unittest.main()
