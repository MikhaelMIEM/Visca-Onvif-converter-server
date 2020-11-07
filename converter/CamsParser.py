import json
from json import JSONDecodeError
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)


class GoogleSheetsCamsParser:
    def __init__(self, json_keyfile="resources-parser.json", spreadsheet_name="visca_onvif_converter_config"):
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
        client = gspread.authorize(creds)
        self.spreadsheet = client.open(spreadsheet_name)

    def read_config(self):
        i = 0
        cams = {}
        while True:
            worksheet = self.spreadsheet.get_worksheet(i)
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


def read_config(conf_path='visca_onvif_config.txt'):
    try:
        with open(conf_path) as config:
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
