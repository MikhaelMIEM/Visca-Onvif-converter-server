import logging
import argparse
from threading import Thread, Lock
from time import sleep
from datetime import datetime
from copy import deepcopy
from onvif import ONVIFError

from converter.CamCommandTranslator import CamCommandTranslator as Translator
from converter.CamsParser import GoogleSheetsCamsParser, read_config
from converter.LoggingTools import init_logger


logger = logging.getLogger('Server')
lock = Lock()
thread_pool = {}
refresh_every_sec = 20


def get_arguments():
    parser = argparse.ArgumentParser(description="Visca to Onvif command converter")
    parser.add_argument("--use-google", help="Enable google spreadsheet cams fetching", action="store_true")
    parser.add_argument("--json-keyfile", metavar="PATH", help="Google api json creds")
    parser.add_argument("--spreadsheet", metavar="STRING_NAME", help="Google spreadsheet name")
    parser.add_argument("--conf", metavar="PATH", help="Config file path")
    parser.add_argument("--logfile", metavar="PATH", help="Logfile path",
                        default=f"log-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.txt")
    parser.add_argument("--debug", "-d", help="Show console debug messages", action="store_true")
    return parser.parse_args()


class CamStorage:
    def __init__(self, cams={}):
        self.cams = deepcopy(cams)

    def get_all(self):
        return deepcopy(self.cams)

    def set_cams(self, cams):
        self.cams = deepcopy(cams)


class TranslatorThread(Thread):
    def __init__(self, visca_server_port, onvif_cam_addr, onvif_cam_login, onvif_cam_password,
                       cam_storage, lock=None):
        Thread.__init__(self)
        self.stop = False
        self.onvif_cam_addr = onvif_cam_addr
        self.visca_server_port = visca_server_port
        self.onvif_cam_login = onvif_cam_login
        self.onvif_cam_password = onvif_cam_password
        self.cam_storage = cam_storage
        self.translator = Translator(visca_server_port, onvif_cam_addr, onvif_cam_login, onvif_cam_password,
                                cam_storage, lock)

    def run(self):
        while self.onvif_cam_addr in self.cam_storage.get_all() and not self.stop:
            try:
                self.translator.run_once()
            except ONVIFError as e:
                logger.error(e)


def start_new_threads(cams):
    for onvif_cam_addr in cams:
        if onvif_cam_addr not in thread_pool:
            visca_port = cams[onvif_cam_addr]["visca_server_port"]
            login = cams[onvif_cam_addr]["onvif_cam_login"]
            password = cams[onvif_cam_addr]["onvif_cam_password"]
            used_ports = {thread.translator.visca_port for thread in thread_pool.values()}
            if visca_port in used_ports:
                logger.error(f'Port "{visca_port}" is already used. '
                             f'Please define another port in config for {onvif_cam_addr}')
                continue
            try:
                thread_pool[onvif_cam_addr] = TranslatorThread(visca_port, onvif_cam_addr, login, password,
                                                               cam_storage)
            except Exception as e:
                logger.error('Check config params.' + str(e))
                continue
            thread_pool[onvif_cam_addr].start()


def clear_dead_threads():
    for thread in list(thread_pool.keys()):
        if not thread_pool[thread].is_alive():
            thread_pool.pop(thread)


def stop_altered_threads(cams):
    for onvif_cam_addr in cams:
        if onvif_cam_addr in thread_pool\
                and is_params_changed(thread_pool[onvif_cam_addr], cams[onvif_cam_addr], onvif_cam_addr):
            thread_pool[onvif_cam_addr].stop = True


def is_params_changed(translator, cam, new_onvif_cam_addr):
    return not (translator.onvif_cam_addr == new_onvif_cam_addr and
                translator.visca_server_port == cam['visca_server_port'] and
                translator.onvif_cam_login == cam['onvif_cam_login'] and
                translator.onvif_cam_password == cam['onvif_cam_password'])


if __name__ == '__main__':
    args = get_arguments()
    init_logger(args.logfile, debug=args.debug)
    cam_storage = CamStorage()
    google_sheet = None

    logger.info(
        "Visca to Onvif converter has been started. "
        + ('Google sheets' if args.use_google else "File")
        + " config is chosen"
    )

    try:
        if args.use_google:
            if not args.json_keyfile:
                logger.error('Exit. No google api json keyfile specified')
                exit(1)
            elif not args.spreadsheet:
                logger.error('Exit. No google spreadsheet name specified')
                exit(1)
            else:
                google_sheet = GoogleSheetsCamsParser(args.json_keyfile, args.spreadsheet)
        elif not args.conf:
            logger.error('Exit. No cameras json config defined')
            exit(1)
    except Exception as e:
        logger.error("Exit. Cannot connect to google sheet with current parameters. " + str(e))
        exit(1)

    while True:
        try:
            if args.use_google:
                cams = google_sheet.read_config()
            else:
                cams = read_config(args.conf)
        except Exception as e:
            logger.error('Error occur during cams fetching. ' + str(e))
            cams = {}

        lock.acquire()
        cam_storage.set_cams(cams)
        lock.release()

        stop_altered_threads(cams)
        clear_dead_threads()
        start_new_threads(cams)

        sleep(refresh_every_sec)
