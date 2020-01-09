from ViscaCommandClassificator import classify_visca_command
from ViscaCommandFormer import form_visca_command
import socket
import logging

logger = logging.getLogger(__name__)


class OneCamCommandTranslator:
    def __init__(self,  server_addr, preset_range={'min': 1, 'max': 20}):
        self.__server_addr = server_addr
        self.__visca_socket = self.__create_socket()
        self.__preset_range = preset_range
        self.__current_preset = self.__preset_range['min']

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
            'CAM_FocusPosInq': self.__CAM_FocusPosInq_handler,
            'Pan_tiltDrive': self.__Pan_tiltDrive_handler,
            'CAM_Zoom': self.__CAM_Zoom_handler,
            'Home': self.__Home_handler
        }

        command = classify_visca_command(data)
        command_name = command['command']
        command_handler = COMMAND_HANDLER_DEFINER[command_name]
        command_handler(command, client_addr)

    def __unknown_handler(self, command, client_addr):
        if 'x' in command:
            x = command['x']
            z = x + 8
        else:
            z = 1
        visca_command_description = {
            'Command': 'Syntax_Error',
            'z': z
        }
        visca_responce = form_visca_command(visca_command_description)
        self.__send(visca_responce, client_addr)

    def __Pan_tiltPosInq_handler(self, command, client_addr):
        x = command['x']
        y = x + 8
        self.__evaluate_current_preset()
        visca_command_description = {
            'Command': 'Pan-tiltPosInq',
            'wwww': self.__current_preset,
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

    def __Pan_tiltDrive_handler(self, command, client_addr):
        if command['function'] == 'AbsolutePosition':
            preset_num = command['YYYY']
            print(preset_num)
            return
        if command['function'] == 'Stop':
            print('stop')
            return

        pan = command['VV'] / 0x18
        tilt = command['WW'] / 0x14
        if command['function'] == 'Up':
            pan = 0
        elif command['function'] == 'Down':
            pan = 0
            tilt = -tilt
        elif command['function'] == 'Left':
            tilt = 0
            pan = -pan
        elif command['function'] == 'Right':
            tilt = 0
        elif command['function'] == 'Upleft':
            pan = -pan
        elif command['function'] == 'DownRight':
            tilt = -tilt
        elif command['function'] == 'DownLeft':
            pan = -pan
            tilt = -tilt
        print(pan, tilt)

    def __CAM_Zoom_handler(self, command, client_addr):
        zoom = command['p'] / 7
        if command['function'] == 'Wide':
            zoom = -zoom
        print(zoom)

    def __Home_handler(self, command, client_addr):
        pass
        print('Home')

    def __evaluate_current_preset(self):
        self.__current_preset += 1
        if self.__current_preset > self.__preset_range['max'] or self.__current_preset < self.__preset_range['min']:
            self.__current_preset = self.__preset_range['min']
