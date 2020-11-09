# Visca to Onvif converter server
This is a **Visca over udp** to **Onvif** command converter which is implemented as server

## Converter specifics
Converter developed to use **Vmix** video production software functionality with *Onvif* cameras. In fact,
*Vmix* do not allows to handle *Onvif* protocol but works perfectly with lots of other control protocols such as 
*Visca over udp*. So the main idea behind this server is to connect *Vmix* software and 
*Onvif* cameras through server-mediator.

In practice, converter is a udp socket server 
which emulates *Visca over udp* camera and translate received
commands into *Onvif* protocol commands.

![](images/1.png)

Now available pan, tilt and zoom movements and go to home position. 
Additionally, *Vmix* allows to create camera preset and remember it's position as *Visca* camera coordinates.
Usually, cheap *Onvif* cameras deviate from protocol standard and can not response it's coordinates, so this feature 
is implemented through *Onvif* preset setting logic.

# Usage
To experience full benefit from this converter recommended to use it paired with **Vmix**

Converter can be configured by either *file config* or *google sheets* document. By default *file config* is used.

## File config
Config file path specified through `--conf` argument and should follow the next json structure:

```json
{
    "cams": [
        {
            "cam_ip": "192.168.0.1",
            "cam_port": 80,
            "cam_login": "admin",
            "cam_password": "password",
            "visca_server_port": 10000,
            "preset_client_range": {
                "192.168.1.1": {
                    "min": 21,
                    "max": 30
                },
                "192.168.1.2": {
                    "min": 11,
                    "max": 20
                },
                "default": {
                    "min": 21,
                    "max": 30
                }
            }
        },
        {
            "cam_ip": "192.168.0.2",
            "cam_port": 80,
            "cam_login": "admin",
            "cam_password": "password",
            "visca_server_port": 10001,
            "preset_client_range": {
                "192.168.1.1": {
                    "min": 21,
                    "max": 30
                },
                "192.168.1.2": {
                    "min": 11,
                    "max": 20
                },
                "default": {
                    "min": 21,
                    "max": 30
                }
            }
        }
    ]
}
```

As can be seen, `cam_ip`, `cam_port`, `cam_login` and `cam_password` fields describe *Onvif* camera that should be controlled,
`visca_server_port` is a udp port converter reads *visca* commands from and translate it to the *Onvif* camera;
`preset_client_range` contains clients addresses and related *Onvif* preset range. Once server receive *visca* coordinates
fetching request from specified in config client, it creates preset in *Onvif* camera with `min` field value and send
back to the client this value instead of real coordinates. During the next fetching coordinates request from the same client
next in a row value will be used as a preset number and so on until `max` value is reached. Then preset appointment 
starts over from `min` value.

In the case of *visca* client wants to set camera in the particular position, which is stored as camera coordinates, it
send command to go to this position. Converter translate it to the `Onvif` camera as go to preset command with related number.

`default` client address specified preset range for all unrecognised clients

![](images/2.png)

Also server reads file config every 30 seconds so no needed to restart server to refresh cameras data, 
just put it in the file and save will be enough

## Google sheets config

Another way to configure server is to use *Google sheets*