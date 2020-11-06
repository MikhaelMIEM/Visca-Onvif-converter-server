import logging

logger = logging.getLogger(__name__)

import zeep
from onvif import ONVIFCamera, ONVIFError
from datetime import timedelta


# MONKEY PATCH
def zeep_pythonvalue(self, xmlvalue):
    return xmlvalue


zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue


ONVIFCameraControlError = ONVIFError


class ONVIFCameraControl:
    def __init__(self, addr, login, password):
        self.__check_addr(addr)
        logger.info(f'Initializing camera {addr}')

        self.__cam = ONVIFCamera(addr[0], addr[1], login, password)

        self.__media_service = self.__cam.create_media_service()
        self.__ptz_service = self.__cam.create_ptz_service()
        self.__imaging_service = self.__cam.create_imaging_service()

        self.__profile = self.__media_service.GetProfiles()[0]
        self.__video_source = self.__get_video_sources()[0]
        self.__status = self.__ptz_service.GetStatus({'ProfileToken': self.__profile.token})

        logging.info(f'Initialized camera at {addr} successfully')

    def get_stream_uri(self, protocol='UDP', stream='RTP-Unicast'):
        """
        :param protocol
            string 'UDP', 'TCP', 'RTSP', 'HTTP'
        :param stream
             string either 'RTP-Unicast' or 'RTP-Multicast'
        WARNING!!!
        Some cameras return invalid stream uri
        RTP unicast over UDP: StreamType = "RTP_Unicast", TransportProtocol = "UDP"
        RTP over RTSP over HTTP over TCP: StreamType = "RTP_Unicast", TransportProtocol = "HTTP"
        RTP over RTSP over TCP: StreamType = "RTP_Unicast", TransportProtocol = "RTSP"
        """
        logger.info(f'Getting stream uri {protocol} {stream}')
        request = self.__media_service.create_type('GetStreamUri')
        request.ProfileToken = self.__profile.token
        request.StreamSetup = {'Stream': stream, 'Transport': {'Protocol': protocol}}
        return self.__media_service.GetStreamUri(request)

    def set_brightness(self, brightness):
        """
        :param brightness:
            float in range [0, 100]
        """
        logger.info(f'Settings brightness')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Brightness = brightness
        self.__set_imaging_settings(imaging_settings)

    def set_color_saturation(self, color_saturation):
        """
        :param color_saturation:
            float in range [0, 100]
        """
        logger.info(f'Settings color_saturation')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.ColorSaturation = color_saturation
        self.__set_imaging_settings(imaging_settings)

    def set_contrast(self, contrast):
        """
        :param contrast:
            float in range [0, 100]
        """
        logger.info(f'Settings contrast')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Contrast = contrast
        self.__set_imaging_settings(imaging_settings)

    def set_sharpness(self, sharpness):
        """
        :param sharpness:
            float in range [0, 100]
        """
        logger.info(f'Settings sharpness')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Sharpness = sharpness
        self.__set_imaging_settings(imaging_settings)

    def set_focus_mode(self, mode='AUTO'):
        """
        :param mode:
            string, can be either 'AUTO' or 'MANUAL'
        """
        logger.info(f'Settings focus mode')
        imaging_settings = self.__get_imaging_settings()
        imaging_settings.Focus.AutoFocusMode = mode
        self.__set_imaging_settings(imaging_settings)

    def move_focus_continuous(self, speed):
        """
        :param speed:
            float in range [-1,1]
        """
        logger.info(f'Doing move focus continuous')
        request = self.__imaging_service.create_type('Move')
        request.VideoSourceToken = self.__video_source.token
        request.Focus = self.__get_move_options()
        request.Focus.Continuous.Speed = speed
        self.__imaging_service.Move(request)

    def move_focus_absolute(self, position, speed=1):
        """
        :param position:
            float in range [0,1]
        :param speed:
            float in range [0,1]
        """
        logger.info(f'Doing move focus absolute')
        request = self.__imaging_service.create_type('Move')
        request.VideoSourceToken = self.__video_source.token
        request.Focus = self.__get_move_options()
        request.Focus.Absolute.Position = position
        request.Focus.Absolute.Speed = speed
        self.__imaging_service.Move(request)

    def stop_focus(self):
        logger.info(f'Stoping focus')
        self.__imaging_service.Stop(self.__video_source.token)

    def set_preset(self, preset_token=None, preset_name=None):
        """
        :param preset_token:
            unsigned int, usually in range [1, 128] dependent on camera
        :param preset_name:
            string
            if None then duplicate preset_token
        """
        logger.info(f'Setting preset {preset_token} ({preset_name})')
        request = self.__ptz_service.create_type('SetPreset')
        request.ProfileToken = self.__profile.token
        request.PresetToken = preset_token
        request.PresetName = preset_name
        return self.__ptz_service.SetPreset(request)

    def goto_preset(self, preset_token, ptz_velocity=(1.0, 1.0, 1.0)):
        """
        :param preset_token:
            unsigned int
        :param ptz_velocity:
            tuple (pan,tilt,zoom) where
            pan tilt and zoom in range [0,1]
        """
        logger.info(f'Moving to preset {preset_token}, speed={ptz_velocity}')
        request = self.__ptz_service.create_type('GotoPreset')
        request.ProfileToken = self.__profile.token
        request.PresetToken = preset_token
        request.Speed = self.__status.Position
        vel = request.Speed
        vel.PanTilt.x, vel.PanTilt.y = ptz_velocity[0], ptz_velocity[1]
        vel.Zoom.x = ptz_velocity[2]
        return self.__ptz_service.GotoPreset(request)

    def get_presets(self):
        logger.debug(f'Getting presets')
        return self.__ptz_service.GetPresets(self.__profile.token)

    def get_brightness(self):
        logger.info(f'Getting brightness')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.Brightness

    def get_color_saturation(self):
        logger.info(f'Getting color_saturation')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.ColorSaturation

    def get_contrast(self):
        logger.info(f'Getting contrast')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.Contrast

    def get_sharpness(self):
        logger.info(f'Getting sharpness')
        imaging_settings = self.__get_imaging_settings()
        return imaging_settings.Sharpness

    def move_continuous(self, ptz_velocity, timeout=None):
        """
        :param ptz_velocity:
            tuple (pan,tilt,zoom) where
            pan tilt and zoom in range [-1,1]
        """
        logger.info(f'Continuous move {ptz_velocity} {"" if timeout is None else " for " + str(timeout)}')
        req = self.__ptz_service.create_type('ContinuousMove')
        req.Velocity = self.__status.Position
        req.ProfileToken = self.__profile.token
        vel = req.Velocity
        vel.PanTilt.x, vel.PanTilt.y = ptz_velocity[0], ptz_velocity[1]
        vel.Zoom.x = ptz_velocity[2]
        # force default space
        vel.PanTilt.space, vel.Zoom.space = None, None
        if timeout is not None:
            if type(timeout) is timedelta:
                req.Timeout = timeout
            else:
                raise TypeError('timeout parameter is of datetime.timedelta type')
        self.__ptz_service.ContinuousMove(req)

    def move_absolute(self, ptz_position, ptz_velocity=(1.0, 1.0, 1.0)):
        logger.info(f'Absolute move {ptz_position}')
        req = self.__ptz_service.create_type['AbsoluteMove']
        req.ProfileToken = self.__profile.token
        pos = req.Position
        pos.PanTilt.x, pos.PanTilt.y = ptz_position[0], ptz_position[1]
        pos.Zoom.x = ptz_position[2]
        vel = req.Speed
        vel.PanTilt.x, vel.PanTilt.y = ptz_velocity[0], ptz_velocity[1]
        vel.Zoom.x = ptz_velocity[2]
        self.__ptz_service.AbsoluteMove(req)

    def move_relative(self, ptz_position, ptz_velocity=(1.0, 1.0, 1.0)):
        logger.info(f'Relative move {ptz_position}')
        req = self.__ptz_service.create_type['RelativeMove']
        req.ProfileToken = self.__profile.token
        pos = req.Translation
        pos.PanTilt.x, pos.PanTilt.y = ptz_position[0], ptz_position[1]
        pos.Zoom.x = ptz_position[2]
        vel = req.Speed
        vel.PanTilt.x, vel.PanTilt.y = ptz_velocity[0], ptz_velocity[1]
        vel.Zoom.x = ptz_velocity[2]
        self.__ptz_service.RelativeMove(req)

    def go_home(self):
        logger.info(f'Moving home')
        req = self.__ptz_service.create_type('GotoHomePosition')
        req.ProfileToken = self.__profile.token
        self.__ptz_service.GotoHomePosition(req)

    def stop(self):
        logger.info(f'Stopping movement')
        self.__ptz_service.Stop({'ProfileToken': self.__profile.token})

    def __get_move_options(self):
        request = self.__imaging_service.create_type('GetMoveOptions')
        request.VideoSourceToken = self.__video_source.token
        return self.__imaging_service.GetMoveOptions(request)

    def __get_options(self):
        logger.debug(f'Getting options')
        request = self.__imaging_service.create_type('GetOptions')
        request.VideoSourceToken = self.__video_source.token
        return self.__imaging_service.GetOptions(request)

    def __get_video_sources(self):
        logger.debug(f'Getting video source configurations')
        request = self.__media_service.create_type('GetVideoSources')
        return self.__media_service.GetVideoSources(request)

    def __get_ptz_conf_opts(self):
        logger.debug(f'Getting configuration options')
        request = self.__ptz_service.create_type('GetConfigurationOptions')
        request.ConfigurationToken = self.__profile.PTZConfiguration.token
        return self.__ptz_service.GetConfigurationOptions(request)

    def __get_configurations(self):
        logger.debug(f'Getting configurations')
        request = self.__ptz_service.create_type('GetConfigurations')
        return self.__ptz_service.GetConfigurations(request)[0]

    def __get_node(self, node_token):
        logger.debug(f'Getting node {node_token}')
        request = self.__ptz_service.create_type('GetNode')
        request.NodeToken = node_token
        return self.__ptz_service.GetNode(request)

    def __set_imaging_settings(self, imaging_settings):
        logger.debug(f'Setting imaging settings')
        request = self.__imaging_service.create_type('SetImagingSettings')
        request.VideoSourceToken = self.__video_source.token
        request.ImagingSettings = imaging_settings
        return self.__imaging_service.SetImagingSettings(request)

    def __get_imaging_settings(self):
        request = self.__imaging_service.create_type('GetImagingSettings')
        request.VideoSourceToken = self.__video_source.token
        return self.__imaging_service.GetImagingSettings(request)

    def __check_addr(self, addr):
        if not isinstance(addr, tuple) or not isinstance(addr[0], str) or not isinstance(addr[1], int):
            raise TypeError(f'addr must be of type tuple(str, int)')