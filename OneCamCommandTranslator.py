from ViscaCommandClassificator import classify_visca_command
from ViscaCommandFormer import form_visca_command
from ONVIFCameraControl import ONVIFCameraControl
import socket
from select import select
import logging

logger = logging.getLogger(__name__)


class OneCamCommandTranslator:
    def __init__(self, visca_server_addr, onvif_cam_addr, onvif_cam_login, onvif_cam_password,
                 preset_ranges_per_client, lock=None):
        logger.info(f'Initializing service {visca_server_addr} -> {onvif_cam_addr}')

        self.__onvif_cam_addr = onvif_cam_addr
        self.__visca_server_addr = visca_server_addr
        self.__visca_socket = self.__create_socket()
        self.__monitored_socket = [self.__visca_socket]
        self.__preset_ranges = preset_ranges_per_client
        self.__current_preset = {}
        self.__update_current_preset_ranges()
        self.__cam = ONVIFCameraControl(onvif_cam_addr, onvif_cam_login, onvif_cam_password)
        self.lock = lock

        logger.info(f'Initializing service {visca_server_addr} -> {onvif_cam_addr} complete')

    def __create_socket(self):
        logger.debug(f'Create socket')

        visca_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        visca_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        visca_socket.bind(self.__visca_server_addr)

        logger.debug(f'Socket created')

        return visca_socket

    def __update_current_preset_ranges(self):
        if self.lock is not None:
            self.lock.acquire()

        preset_ranges = self.__preset_ranges[self.__onvif_cam_addr]

        for client, preset_range in preset_ranges:
            if client not in self.__current_preset:
                self.__current_preset[client] = preset_range['min']
            elif not self.__is_preset_in_range(client):
                self.__current_preset[client] = preset_range['min']

        for client in list(self.__current_preset.items()):
            if client not in preset_ranges:
                self.__current_preset.pop(client)

        if self.lock is not None:
            self.lock.release()

    def run_once(self):
        if self.__is_socket_ready():
            message, client_addr = self.__receive_visca_message()
            self.__update_current_preset_ranges()
            self.__handle_byte_message(message, client_addr)

    def __is_socket_ready(self):
        ready_to_read_socket, _, _ = select(self.__monitored_socket, [], [])
        return bool(ready_to_read_socket)

    def __receive_visca_message(self):
        data, client_addr = self.__visca_socket.recvfrom(16)
        logger.debug(f'Received {data.hex()} from {client_addr}')
        return data, client_addr

    def __send_to_visca_controller(self, data, addr):
        logger.debug(f'Sending {data.hex()} to {addr}')
        self.__visca_socket.sendto(data, addr)

    def __handle_byte_message(self, message, client_addr):
        COMMAND_HANDLER_DEFINER = {
            'unknown': self.__unknown_command_handler,
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

    def __unknown_command_handler(self, command, client_addr):
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
        if client_addr in self.__current_preset:
            self.__evaluate_current_preset(client_addr)
            current_preset = self.__current_preset[client_addr]
        else:
            current_preset = 0
        visca_command_description = {
            'Command': 'Pan-tiltPosInq',
            'wwww': current_preset,
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
            if client_addr in self.__current_preset:
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

    def __evaluate_current_preset(self, client_addr):
        if self.lock is not None:
            self.lock.acquire()

        self.__current_preset[client_addr] += 1
        if not self.__is_preset_in_range(client_addr):
            self.__current_preset[client_addr] = self.__preset_ranges[self.__onvif_cam_addr][client_addr]['min']

        if self.lock is not None:
            self.lock.release()

    def __is_preset_in_range(self, client_addr):
        preset_range = self.__preset_ranges[self.__onvif_cam_addr][client_addr]
        return preset_range['max'] >= self.__current_preset[client_addr] >= preset_range['min']

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
