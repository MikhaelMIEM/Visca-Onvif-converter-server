from ViscaCommandClassificator import classify_visca_command
from ViscaCommandFormer import form_visca_command
from OneCamCommandTranslator import OneCamCommandTranslator as Translator

received_bytes = b'\x81\x01\x06\x01\x14\x13\x01\x02\xFF' #Pan_tiltDrive upleft
received_bytes = b'\x81\x01\x06\x02\x14\x14\x03\x0F\x01\x02\x0A\x01\x01\x01\xFF' #Pan_tiltDrive AbsolutePosition
received_bytes = b'\x85\x01\x04\x07\x3F\xFF'  # CAM_Zoom Tele Wide
received_bytes = b'\x82\x01\x06\x04\xFF'  # Home
received_bytes = b'\x85\x09\x06\x12\xFF'  # Pan-tiltPosInq

print(classify_visca_command(received_bytes))

description = {'Command': 'Pan-tiltPosInq', 'x': 5}
description = {'Command': 'Pan-tiltPosInq', 'wwww': b'\x12\x34', 'zzzz': 0x5678, 'y': 6}
description = {'Command': 'CAM_FocusPosInq', 'p': 1, 'q': 2, 'r': 3, 's': 4, 'y': 5}
print(form_visca_command(description))

server_addr = ('localhost', 1337)
translator = Translator(server_addr)

translator.run_once()
translator.run_once()
translator.run_once()