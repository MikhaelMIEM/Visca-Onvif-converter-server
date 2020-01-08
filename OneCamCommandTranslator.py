from ViscaCommandClassificator import classify_visca_command
from ViscaCommandFormer import form_visca_command
import ONVIFCameraControl
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
        return visca_socket

    def run_once(self):
        data, client_addr = self.__receive()
        self.__process_command(data, client_addr)

    def __receive(self):
        data, client_addr = self.__visca_socket.recvfrom(16)
        logger.debug(f'Received {data.hex()} from {client_addr}')
        return data, client_addr

    def __send(self, data, addr):
        logger.debug(f'Sending {data.hex()} to {addr}')
        self.__visca_socket.sendto(data, addr)

    def __process_command(self, data, client_addr):
        COMMAND_HANDLER_DEFINER = {
            'unknown': self.__unknown_handler,
            'Pan-tiltPosInq': self.__Pan_tiltPosInq_handler,
            'CAM_ZoomPosInq': self.__CAM_ZoomPosInq_handler,
            'CAM_FocusPosInq': self.__CAM_FocusPosInq_handler
        }

        command = classify_visca_command(data)
        command_name = command['command']
        command_handler = COMMAND_HANDLER_DEFINER[command_name]
        command_handler(command, client_addr)

    def __unknown_handler(self, command, client_addr):
        pass

    def __Pan_tiltPosInq_handler(self, command, client_addr):
        x = command['x']
        y = x + 8
        visca_command_description = {
            'Command': 'Pan-tiltPosInq',
            'wwww': 0,
            'zzzz': 0,
            'y': y
        }
        visca_responce = form_visca_command(visca_command_description)
        self.__send(visca_responce, client_addr)

    def __CAM_ZoomPosInq_handler(self, command, client_addr):
        x = command['x']
        y = x + 8
        visca_command_description = {
            'Command': 'CAM_ZoomPosInq',
            'p': 0,
            'q': 0,
            'r': 0,
            's': 0,
            'y': y
        }
        visca_responce = form_visca_command(visca_command_description)
        self.__send(visca_responce, client_addr)

    def __CAM_FocusPosInq_handler(self, command, client_addr):
        x = command['x']
        y = x + 8
        visca_command_description = {
            'Command': 'CAM_FocusPosInq',
            'p': 0,
            'q': 0,
            'r': 0,
            's': 0,
            'y': y
        }
        visca_responce = form_visca_command(visca_command_description)
        self.__send(visca_responce, client_addr)
