from threading import Thread, Lock
from .CamCommandTranslator import CamCommandTranslator as Translator
import logging
import json
from time import sleep
from copy import deepcopy
from onvif import ONVIFError
from json import JSONDecodeError
import gspread
from oauth2client.service_account import ServiceAccountCredentials


logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

lock = Lock()
preset_ranges = {}
thread_pool = {}
refresh_every_sec = 10

#Google sheets vars
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("resources-parser.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("visca_onvif_converter_config")


class TranslatorThread(Thread):
    def __init__(self, visca_server_port, onvif_cam_addr, onvif_cam_login, onvif_cam_password,
                       cam_storage, lock=None):
        Thread.__init__(self)
        self.need_refresh = False
        self.onvif_cam_addr = onvif_cam_addr
        self.visca_server_port = visca_server_port
        self.onvif_cam_login = onvif_cam_login
        self.onvif_cam_password = onvif_cam_password
        self.cam_storage = cam_storage
        self.translator = Translator(visca_server_port, onvif_cam_addr, onvif_cam_login, onvif_cam_password,
                                cam_storage, lock)

    def run(self):
        while self.onvif_cam_addr in self.cam_storage.get_all() and not self.need_refresh:
            try:
                self.translator.run_once()
            except ONVIFError as e:
                logger.error(e)


class CamStorage:
    def __init__(self, cams={}):
        self.cams = deepcopy(cams)

    def get_all(self):
        return deepcopy(self.cams)

    def set_cams(self, cams):
        self.cams = deepcopy(cams)


def clear_dead_threads():
    for thread in list(thread_pool.keys()):
        if not thread_pool[thread].is_alive():
            thread_pool.pop(thread)


def read_config():
    try:
        with open('visca_onvif_config.txt') as config:
            data = json.load(config)
    except JSONDecodeError as e:
        logger.error(f'Wrong config format. Check json syntax.' + str(e))
        data = {"cams": {}}
        
    cams = {}

    try:
        for cam in data["cams"]:
                cam_addr = (cam["cam_ip"], cam["cam_port"])
                cams[cam_addr] = {}
                cams[cam_addr]["preset_client_range"] = cam["preset_client_range"]
                cams[cam_addr]["visca_server_port"] = cam["visca_server_port"]
                cams[cam_addr]["onvif_cam_login"] = cam["cam_login"]
                cams[cam_addr]["onvif_cam_password"] = cam["cam_password"]
    except KeyError as e:
        cams = {}
        logger.error(f'Wrong config format.' + str(e))

    return cams


def read_google_sheets_config():
    i = 0
    cams = {}
    while True:
        worksheet = spreadsheet.get_worksheet(i)
        try:
            data = worksheet.get_all_values()
        except AttributeError:
            break
        ip = data[1][0]
        port = int(data[1][1])
        addr = (ip, port)
        cam = {"onvif_cam_login": data[1][2], "onvif_cam_password": data[1][3], "visca_server_port": int(data[1][4]),
               "preset_client_range": {}}
        preset_range = cam["preset_client_range"]
        for line in data[4:]:
            preset_range[line[0]] = {}
            prange = preset_range[line[0]]
            prange['min'] = int(line[1])
            prange['max'] = int(line[2])
        cams[addr] = cam
        i += 1
    return cams


def is_params_changed(translator, cam, new_onvif_cam_addr):
    return not (translator.onvif_cam_addr == new_onvif_cam_addr and
                translator.visca_server_port == cam['visca_server_port'] and
                translator.onvif_cam_login == cam['onvif_cam_login'] and
                translator.onvif_cam_password == cam['onvif_cam_password'])


def refresh_threads(cams):
    for onvif_cam_addr in cams:
        if onvif_cam_addr not in thread_pool:
            visca_port = cams[onvif_cam_addr]["visca_server_port"]
            login = cams[onvif_cam_addr]["onvif_cam_login"]
            password = cams[onvif_cam_addr]["onvif_cam_password"]
            try:
                thread_pool[onvif_cam_addr] = TranslatorThread(visca_port, onvif_cam_addr, login, password,
                                                               cam_storage)
            except Exception as e:
                logger.error('Check config params.' + str(e))
                continue
            thread_pool[onvif_cam_addr].start()
        elif is_params_changed(thread_pool[onvif_cam_addr], cams[onvif_cam_addr], onvif_cam_addr):
            thread_pool[onvif_cam_addr].need_refresh = True


if __name__ == '__main__':
    cam_storage = CamStorage()

    while True:
        clear_dead_threads()
        try:
            cams = read_google_sheets_config()
        except Exception:
            cams = {}

        lock.acquire()
        cam_storage.set_cams(cams)
        lock.release()

        refresh_threads(cams)
        sleep(refresh_every_sec)
