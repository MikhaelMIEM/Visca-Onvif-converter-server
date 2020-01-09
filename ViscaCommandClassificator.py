def classify_visca_command(message):
    UNNKNOWN_COMMAND = {'command': 'unknown'}

    def is_message_CommandCancel():
        return message[0] // 0x10 == 0x08 and message[1] == 0x21

    def is_message_control():
        return message[0] // 0x10 == 0x08 and message[1] == 0x01

    def is_message_inquiry():
        return message[0] // 0x10 == 0x08 and message[1] == 0x09

    def handle_CommandCancel_message():
        classified_command = {'command': 'CommandCancel'}
        x = message[0] % 0x10
        classified_command['x'] = x
        return classified_command

    def handle_control_message():
        command_indicator = message[2:4]
        try:
            command_handler = CONTROL_COMMAND_HANDLER_DEFINER[command_indicator]
        except KeyError:
            return UNNKNOWN_COMMAND
        classified_command = command_handler()
        x = message[0] % 0x10
        classified_command['x'] = x
        return classified_command

    def handle_inquiry_message():
        command_indicator = message[2:4]
        try:
            command_handler = INQUIRY_COMMAND_HANDLER_DEFINER[command_indicator]
        except KeyError:
            return UNNKNOWN_COMMAND
        classified_command = command_handler()
        x = message[0] % 0x10
        classified_command['x'] = x
        return classified_command

    def Home():
        classified_command = {'command': 'Home',
                              'function': 'Home'}
        return classified_command

    def CAM_Zoom():
        args = message[2:-1]
        p = args[2] % 0x10

        if args[2] // 0x10 == 0x02:
            function = 'Tele'
        elif args[2] // 0x10 == 0x03:
            function = 'Wide'
        elif args[2] == 0:
            function = 'Stop'

        classified_command = {'command': 'CAM_Zoom',
                              'function': function,
                              'p': p}
        return classified_command

    def Pan_tiltDrive():
        args = message[2:-1]
        function_definer = args[1]

        args = args[2:]
        VV = args[0]
        WW = args[1]

        args = args[2:]
        if function_definer == 0x01:
            CONTINUOUS_MOVE_FUNCTION_DEFINER = {
                b'\x03\x03': 'Stop',
                b'\x02\x02': 'DownRight',
                b'\x01\x02': 'DownLeft',
                b'\x02\x01': 'Upright',
                b'\x01\x01': 'Upleft',
                b'\x02\x03': 'Right',
                b'\x01\x03': 'Left',
                b'\x03\x02': 'Down',
                b'\x03\x01': 'Up',
            }

            args = args[-3:]
            if args not in CONTINUOUS_MOVE_FUNCTION_DEFINER:
                return UNNKNOWN_COMMAND

            function = CONTINUOUS_MOVE_FUNCTION_DEFINER[args]

            classified_command = {'command': 'Pan_tiltDrive',
                                  'function': function,
                                  'VV': VV,
                                  'WW': WW}

            return classified_command

        elif function_definer == 0x02:
            function = 'AbsolutePosition'
            YYYY = get_YYYY_from_0Y0Y0Y0Y(args[0:4])
            ZZZZ = get_YYYY_from_0Y0Y0Y0Y(args[4:8])

            classified_command = {'command': 'Pan_tiltDrive',
                                  'function': function,
                                  'VV': VV,
                                  'WW': WW,
                                  'YYYY': YYYY,
                                  'ZZZZ': ZZZZ}
        return classified_command

    def Pan_tiltPosInq():
        classified_command = {'command': 'Pan-tiltPosInq'}
        return classified_command

    def CAM_ZoomPosInq():
        classified_command = {'command': 'CAM_ZoomPosInq'}
        return classified_command

    def CAM_FocusPosInq():
        classified_command = {'command': 'CAM_FocusPosInq'}
        return classified_command

    def get_YYYY_from_0Y0Y0Y0Y(y):
        return bytes([y[0] << 4 | y[1], y[2] << 4 | y[3]])

    CONTROL_COMMAND_HANDLER_DEFINER = {
        b'\x06\x04': Home,
        b'\x04\x07': CAM_Zoom,
        b'\x06\x01': Pan_tiltDrive,
        b'\x06\x02': Pan_tiltDrive
    }

    INQUIRY_COMMAND_HANDLER_DEFINER = {
        b'\x06\x12': Pan_tiltPosInq,
        b'\x04\x48': CAM_FocusPosInq,
        b'\x04\x47': CAM_ZoomPosInq
    }

    if type(message) is not bytes:
        raise ValueError('Visca command classifier require message of bytes')
    if len(message) < 3:
        return UNNKNOWN_COMMAND
    if is_message_CommandCancel():
        return handle_CommandCancel_message()
    if is_message_control():
        return handle_control_message()
    elif is_message_inquiry():
        return handle_inquiry_message()
    else:
        return UNNKNOWN_COMMAND
