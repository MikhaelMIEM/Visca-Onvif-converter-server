def form_visca_command(description):
    def Ack():
        z = description['z']
        return b''.join([bytes([0x10 * z]), b'\x41\xFF'])

    def Pan_tiltPosInq():
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

    def CAM_ZoomPosInq():
        if 'p' in description and 'q' in description and 'r' in description and 's' in description and\
                'y' in description:
            return ypqts_inquiry_responce()
        elif 'x' in description:
            x = description['x']
            return b''.join([bytes([0x80 + x]), b'\x09\x04\x47\xFF'])
        else:
            raise KeyError('Unknown command description')

    def CAM_FocusPosInq():
        if 'p' in description and 'q' in description and 'r' in description and 's' in description and\
                'y' in description:
            return ypqts_inquiry_responce()
        elif 'x' in description:
            x = description['x']
            return b''.join([bytes([0x80 + x]), b'\x09\x04\x48\xFF'])
        else:
            raise KeyError('Unknown command description')

    def ypqts_inquiry_responce():
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
        'Pan-tiltPosInq': Pan_tiltPosInq,
        'CAM_ZoomPosInq': CAM_ZoomPosInq,
        'CAM_FocusPosInq': CAM_FocusPosInq
    }

    if description['Command'] in DESCRIPTION_HANDLER_DEFINER:
        return DESCRIPTION_HANDLER_DEFINER[description['Command']]()
    else:
        raise KeyError('Unknown command name')
