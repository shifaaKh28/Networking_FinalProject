import random  # Importing the random module for generating random numbers
import socket  # Importing the socket module for creating and managing network connections
import struct  # Importing the struct module for working with C-style data structures
import pickle  # Importing the pickle module for serializing and deserializing Python objects
import sys  # Importing the sys module for system-specific parameters and functions

# Constants for QUIC packet flags
LONG_HEADER_FLAG = 1  # Long header flag for QUIC packets
SHORT_HEADER_FLAG = 0  # Short header flag for QUIC packets

def generate_random_hex():
    """
    Generate a random 16-character hexadecimal string.
    
    Returns:
        str: A random 16-character hexadecimal string.
    """
    random_int = random.randint(0, 2**64 - 1)  # Generate a random integer between 0 and (2^64 - 1)
    hex_string = hex(random_int)[2:]  # Convert the integer to hexadecimal and remove the '0x' prefix
    hex_string = hex_string.zfill(16)  # Ensure the hex string is 16 characters long (8 bytes)
    return hex_string

class QUICPacket:
    def __init__(self, flags, dest_conn_id, packet_number, protected_payload: list):
        """
        Initialize a QUICPacket object.

        Args:
            flags (int): Packet flags.
            dest_conn_id (str): Destination connection ID.
            packet_number (int): Packet number.
            protected_payload (list): List of protected payloads.
        """
        self.flags = flags
        self.dest_conn_id = dest_conn_id
        self.packet_number = packet_number
        self.protected_payload = protected_payload

    def encode(self):
        """
        Encode the QUICPacket object using pickle.

        Returns:
            bytes: Encoded QUICPacket object.
        """
        return pickle.dumps(self)
    
    @classmethod
    def decode(cls, data):
        """
        Decode a QUICPacket object from bytes using pickle.

        Args:
            data (bytes): Encoded QUICPacket object.

        Returns:
            QUICPacket: Decoded QUICPacket object.
        """
        return pickle.loads(data)

    def __str__(self):
        """
        Return a string representation of the QUICPacket object.

        Returns:
            str: String representation of the QUICPacket object.
        """
        str = f"Flags: {self.flags} Dest Conn ID: {self.dest_conn_id} Packet Number: {self.packet_number}"
        str +=  " Payload: " 
        for payload in self.protected_payload:
            str += f"{payload.__str__()}"
        str += "\n"
        return str
    
    def size_in_bytes(self):
        """
        Calculate the size of the QUICPacket object in bytes.

        Returns:
            int: Size of the QUICPacket object in bytes.
        """
        flags_size = sys.getsizeof(self.flags)
        dest_conn_id_size = sys.getsizeof(self.dest_conn_id)
        packet_number_size = sys.getsizeof(self.packet_number)
        payload_size = sys.getsizeof(self.protected_payload)
        total_size = flags_size + dest_conn_id_size + packet_number_size + payload_size
        return total_size

class QUICStreamPayload:
    def __init__(self, stream_id, offset, length, finished, stream_data):
        """
        Initialize a QUICStreamPayload object.

        Args:
            stream_id (int): Stream ID.
            offset (int): Offset in the stream.
            length (int): Length of the stream data.
            finished (int): Indicates if the stream is finished (1) or not (0).
            stream_data (bytes): Data of the stream.
        """
        self.stream_id = stream_id
        self.offset = offset
        self.finished = finished
        self.length = length
        self.stream_data = stream_data

    def encode(self):
        """
        Encode the QUICStreamPayload object using pickle.

        Returns:
            bytes: Encoded QUICStreamPayload object.
        """
        return pickle.dumps(self)

    @classmethod
    def decode(cls, data):
        """
        Decode a QUICStreamPayload object from bytes using pickle.

        Args:
            data (bytes): Encoded QUICStreamPayload object.

        Returns:
            QUICStreamPayload: Decoded QUICStreamPayload object.
        """
        return pickle.loads(data) 
    
    def __str__(self):
        """
        Return a string representation of the QUICStreamPayload object.

        Returns:
            str: String representation of the QUICStreamPayload object.
        """
        return f"Stream ID: {self.stream_id} Offset: {self.offset} Finished: {self.finished} Length: {self.length}"

class QUICLongHeader:
    def __init__(self, flags, dest_conn_id, src_conn_id, packet_number):
        """
        Initialize a QUICLongHeader object.

        Args:
            flags (int): Header flags.
            dest_conn_id (str): Destination connection ID.
            src_conn_id (str): Source connection ID.
            packet_number (int): Packet number.
        """
        self.flags = flags
        self.dest_cid = dest_conn_id
        self.src_cid = src_conn_id
        self.packet_number = packet_number

    def encode(self):
        """
        Encode the QUICLongHeader object using pickle.

        Returns:
            bytes: Encoded QUICLongHeader object.
        """
        return pickle.dumps(self)

    @classmethod
    def decode(cls, data):
        """
        Decode a QUICLongHeader object from bytes using pickle.

        Args:
            data (bytes): Encoded QUICLongHeader object.

        Returns:
            QUICLongHeader: Decoded QUICLongHeader object.
        """
        return pickle.loads(data)

class QUICSocket:
    def __init__(self):
        """
        Initialize a QUICSocket object.
        """
        self.__address = None
        self.__dest_cid = None
        self.__src_cid = None
        self.__sockfd = None

    def create_socket(self):
        """
        Create a UDP socket and set necessary socket options.
        """
        self.__sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.__sockfd is None:
            raise RuntimeError("Socket creation failed.")
        self.__sockfd.settimeout(3)
        self.__sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.__sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    def bind(self, address):
        """
        Bind the socket to a specified address.

        Args:
            address (tuple): Address to bind the socket to.
        """
        if self.__sockfd:
            self.__sockfd.bind(address)

    def close(self):
        """
        Close the socket.
        """
        if self.__sockfd:
            self.__sockfd.close()

    def sendto(self, data, address):
        """
        Send data to a specified address.

        Args:
            data (bytes): Data to send.
            address (tuple): Address to send the data to.
        """
        if not self.__sockfd:
            raise RuntimeError("Socket not initialized. Call create_socket() first.")
        try:
            self.__sockfd.sendto(data, address)
        except (KeyboardInterrupt, socket.timeout) as e:
            print(e)
            print("Exiting...")
            self.__sockfd.close()
            exit(0)

    def recvfrom(self, bufsize):
        """
        Receive data from the socket.

        Args:
            bufsize (int): Buffer size for receiving data.

        Returns:
            tuple: Received data and address of the sender.
        """
        if not self.__sockfd:
            raise RuntimeError("Socket not initialized. Call create_socket() first.")
        try:
            return self.__sockfd.recvfrom(bufsize)
        except (KeyboardInterrupt, socket.timeout) as e:
            print(e)
            print("Exiting...")
            self.__sockfd.close()
            exit(0)

    # Setters
    def set_address(self, address):
        """
        Set the address for the socket.

        Args:
            address (tuple): Address to set.
        """
        self.__address = address

    def set_dest_cid(self, dest_cid):
        """
        Set the destination connection ID.

        Args:
            dest_cid (str): Destination connection ID.
        """
        self.__dest_cid = dest_cid

    def set_src_cid(self, src_cid):
        """
        Set the source connection ID.

        Args:
            src_cid (str): Source connection ID.
        """
        self.__src_cid = src_cid

    # Getters
    def get_address(self):
        """
        Get the address of the socket.

        Returns:
            tuple: Address of the socket.
        """
        return self.__address

    def get_dest_cid(self):
        """
        Get the destination connection ID.

        Returns:
            str: Destination connection ID.
        """
        return self.__dest_cid

    def get_src_cid(self):
        """
        Get the source connection ID.

        Returns:
            str: Source connection ID.
        """
        return self.__src_cid

    def get_sockfd(self):
        """
        Get the socket file descriptor.

        Returns:
            socket.socket: Socket file descriptor.
        """
        if not self.__sockfd:
            raise RuntimeError("Socket not initialized. Call create_socket() first.")
        return self.__sockfd

class QUICAck:
    def __init__(self, ack_number, ack_delay):
        """
        Initialize a QUICAck object.

        Args:
            ack_number (int): Acknowledgement number.
            ack_delay (int): Acknowledgement delay.
        """
        self.ack_number = ack_number
        self.ack_delay = ack_delay

    def encode(self):
        """
        Encode the QUICAck object using pickle.

        Returns:
            bytes: Encoded QUICAck object.
        """
        try:
            return pickle.dumps(self)
        except pickle.PickleError as e:
            print(f"Error encoding QUICPacket: {e}")
            return None

    @classmethod
    def decode(cls, data):
        """
        Decode a QUICAck object from bytes using pickle.

        Args:
            data (bytes): Encoded QUICAck object.

        Returns:
            QUICAck: Decoded QUICAck object.
        """
        try:
            return pickle.loads(data)
        except pickle.UnpicklingError as e:
            print(f"Error decoding QUICPacket: {e}")
            return None
