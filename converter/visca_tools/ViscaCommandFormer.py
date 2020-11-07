def form_visca_command(description):
    """
    command former according to:
    https://www.epiphan.com/userguides/LUMiO12x/Content/UserGuides/PTZ/3-operation/VISCAcommands.htm
    description is a dict in format {"Command": "{command name}", "{arg}": "{value}", "z": 1, "y": 2, ...}
    """
    if description['Command'] in DESCRIPTION_HANDLER_DEFINER:
        return DESCRIPTION_HANDLER_DEFINER[description['Command']](description)
    else:
        raise KeyError('Unknown command name')


def Ack(description):
    if 'z' in description:
        z = description['z']
        return b''.join([bytes([0x10 * z]), b'\x41\xFF'])
    else:
        raise KeyError('Unknown command description')


def Syntax_Error(description):
    if 'z' in description:
        z = description['z']
        return b''.join([bytes([0x10 * z]), b'\x60\x02\xFF'])
    else:
        raise KeyError('Unknown command description')


def Pan_tiltPosInq(description):
    if 'wwww' in description and 'zzzz' in description and 'y' in description:
        y = description['y']
        wwww = description['wwww']
        zzzz = description['zzzz']
        return b''.join([bytes([0x10 * y]), b'\x50', get_0w0w0w0w_from_wwww(wwww),
                         get_0w0w0w0w_from_wwww(zzzz), b'\xFF'])
    elif 'x' in description:
        x = description['x']
        return b''.join([bytes([0x80 + x]), b'\x09\x06\x12\xFF'])
    else:
        raise KeyError('Unknown command description')


def CAM_ZoomPosInq(description):
    if 'p' in description and 'q' in description and 'r' in description and 's' in description and\
            'y' in description:
        return ypqts_inquiry_responce(description)
    elif 'x' in description:
        x = description['x']
        return b''.join([bytes([0x80 + x]), b'\x09\x04\x47\xFF'])
    else:
        raise KeyError('Unknown command description')


def CAM_FocusPosInq(description):
    if 'p' in description and 'q' in description and 'r' in description and 's' in description and\
            'y' in description:
        return ypqts_inquiry_responce(description)
    elif 'x' in description:
        x = description['x']
        return b''.join([bytes([0x80 + x]), b'\x09\x04\x48\xFF'])
    else:
        raise KeyError('Unknown command description')


def ypqts_inquiry_responce(description):
    y = description['y']
    p = description['p']
    q = description['q']
    r = description['r']
    s = description['s']
    return b''.join([bytes([0x10 * y]), b'\x50', bytes([p]), bytes([q]), bytes([r]), bytes([s]), b'\xFF'])


def get_0w0w0w0w_from_wwww(wwww):
    if type(wwww) is bytes:
        return b''.join([bytes([wwww[0] // 16, wwww[0] % 16, wwww[1] // 16, wwww[1] % 16])])
    elif type(wwww) is int:
        return b''.join([bytes([wwww // 16**3, wwww // 16**2 % 16, wwww // 16 % 16, wwww % 16])])


DESCRIPTION_HANDLER_DEFINER = {
        'Ack': Ack,
        'Syntax_Error': Syntax_Error,
        'Pan-tiltPosInq': Pan_tiltPosInq,
        'CAM_ZoomPosInq': CAM_ZoomPosInq,
        'CAM_FocusPosInq': CAM_FocusPosInq
    }