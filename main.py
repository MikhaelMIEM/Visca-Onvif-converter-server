from threading import Thread, Lock
from OneCamCommandTranslator import OneCamCommandTranslator as Translator

lock = Lock()
preset_ranges = {}


def run_translator(visca_server_addr, onvif_cam_addr, onvif_cam_login, onvif_cam_password, preset_ranges_per_client, lock):
    translator = Translator(visca_server_addr, onvif_cam_addr, onvif_cam_login, onvif_cam_password,
                            preset_ranges_per_client, lock)
    while onvif_cam_addr in preset_ranges:
        translator.run_once()



if __name__ == '__main__':
    pass
