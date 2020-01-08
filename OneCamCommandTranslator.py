import socket
import logging

logger = logging.getLogger(__name__)


class OneCamCommandTranslator:
    def __init__(self,  server_addr):
        self.__server_addr = server_addr
        self.__visca_socket = self.__create_socket()

    def __create_socket(self):
        visca_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        visca_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        visca_socket.bind(self.__server_addr)
        visca_socket.setblocking(False)
        visca_socket.settimeout(1)
        return visca_socket

    def __receive(self):
        data, addr = self.__visca_socket.recvfrom(16)
        logger.debug(f'Received {data.hex()} from {addr}')
        return data, addr

    def __process_command(self, data):
        print(data.decode())

    def run_once(self):
        try:
            data, addr = self.__receive()
            self.__process_command(data)
        except socket.timeout:
            raise TimeoutError

