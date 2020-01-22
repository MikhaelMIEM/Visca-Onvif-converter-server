from ViscaCommandClassificator import classify_visca_command
from ViscaCommandFormer import form_visca_command
from ONVIFCameraControl import ONVIFCameraControl
import socket
import logging

logger = logging.getLogger(__name__)


class OneCamCommandTranslator:
    def __init__(self,  server_addr, cam_addr, cam_login, cam_password, preset_range={'min': 1, 'max': 20}):
        logger.info(f'Initializing service {server_addr} -> {cam_addr}')

        self.__server_addr = server_addr
        self.__visca_socket = self.__create_socket()
        self.__preset_range = preset_range
        self.__current_preset = self.__preset_range['min']
        self.__cam = ONVIFCameraControl(cam_addr, cam_login, cam_password)

        logger.info(f'Initializing service {server_addr} -> {cam_addr} complete')


    def __create_socket(self):
        logger.debug(f'Create socket')

        visca_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        visca_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        visca_socket.bind(self.__server_addr)

        logger.debug(f'Socket created')

        return visca_socket

    def run_once(self):
        message, client_addr = self.__receive_visca_message()
        self.__handle_byte_message(message, client_addr)

    def __receive_visca_message(self):
        data, client_addr = self.__visca_socket.recvfrom(16)
        logger.debug(f'Received {data.hex()} from {client_addr}')
        return data, client_addr

    def __send_to_visca_controller(self, data, addr):
        logger.debug(f'Sending {data.hex()} to {addr}')
        self.__visca_socket.sendto(data, addr)

    def __handle_byte_message(self, message, client_addr):
        COMMAND_HANDLER_DEFINER = {
            'unknown': self.__unknown_handler,
            'Pan-tiltPosInq': self.__Pan_tiltPosInq_handler,
            'CAM_ZoomPosInq': self.__CAM_ZoomPosInq_handler,
            'CAM_FocusPosInq': self.__CAM_FocusPosInq_handler,
            'Pan_tiltDrive': self.__Pan_tiltDrive_handler,
            'CAM_Zoom': self.__CAM_Zoom_handler,
            'Home': self.__Home_handler
        }

        command = classify_visca_command(message)
        command_name = command['command']
        command_handler = COMMAND_HANDLER_DEFINER[command_name]
        command_handler(command, client_addr)

    def __unknown_handler(self, command, client_addr):
        logger.debug(f'Unknown command. Sending Syntax_Error to visca controller.')
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
        self.__send_to_visca_controller(visca_responce, client_addr)

    def __Pan_tiltPosInq_handler(self, command, client_addr):
        logger.debug(f'Handling Pan_tiltPosInq.')
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
        self.__send_to_visca_controller(visca_responce, client_addr)

    def __CAM_ZoomPosInq_handler(self, command, client_addr):
        logger.debug(f'Handling CAM_ZoomPosInq.')
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
        self.__send_to_visca_controller(visca_responce, client_addr)

    def __CAM_FocusPosInq_handler(self, command, client_addr):
        logger.debug(f'Handling CAM_FocusPosInq.')
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
        self.__send_to_visca_controller(visca_responce, client_addr)

    def __Pan_tiltDrive_handler(self, command, client_addr):
        if command['function'] == 'AbsolutePosition':
            logger.debug(f'Handling Pan_tiltDrive AbsolutePosition (as Onvif goto_preset).')
            preset_num = command['YYYY']
            self.__cam.set_preset(preset_num)
        elif command['function'] == 'Stop':
            logger.debug(f'Handling Pan_tiltDrive Stop (as Onvif stop).')
            self.__cam.stop()
        else:
            logger.debug(f'Handling Pan_tiltDrive (as Onvif move_continuous).')
            pan_velocity, tilt_velocity = self.__get_pan_tilt_velocities_for_move_continuous(command)
            ptz_velocity_vector = (pan_velocity, tilt_velocity, 0)
            self.__cam.move_continuous(ptz_velocity_vector)

    def __CAM_Zoom_handler(self, command, client_addr):
        if command['function'] == 'Stop':
            logger.debug(f'Handling Zoom Stop (as Onvif stop).')
            self.__cam.stop()
        else:
            logger.debug(f'Handling Zoom (as Onvif move_continuous).')
            zoom_velocity = command['p'] / 7
            if command['function'] == 'Wide':
                zoom_velocity = -zoom_velocity
            ptz_velocity_vector = (0, 0, zoom_velocity)
            self.__cam.move_continuous(ptz_velocity_vector)

    def __Home_handler(self, command, client_addr):
        logger.debug(f'Handling Home (as Onvif go_home).')
        self.__cam.go_home()

    def __evaluate_current_preset(self):
        self.__current_preset += 1
        if self.__current_preset > self.__preset_range['max'] or self.__current_preset < self.__preset_range['min']:
            self.__current_preset = self.__preset_range['min']

    def __get_pan_tilt_velocities_for_move_continuous(self, command):
        pan_velocity = command['VV'] / 0x18
        tilt_velocity = command['WW'] / 0x14

        if command['function'] == 'Up':
            pan_velocity = 0
        elif command['function'] == 'Down':
            pan_velocity = 0
            tilt_velocity = -tilt_velocity
        elif command['function'] == 'Left':
            tilt_velocity = 0
            pan_velocity = -pan_velocity
        elif command['function'] == 'Right':
            tilt_velocity = 0
        elif command['function'] == 'Upleft':
            pan_velocity = -pan_velocity
        elif command['function'] == 'DownRight':
            tilt_velocity = -tilt_velocity
        elif command['function'] == 'DownLeft':
            pan_velocity = -pan_velocity
            tilt_velocity = -tilt_velocity
        return pan_velocity, tilt_velocity
