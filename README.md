# Visca to Onvif converter server
This is a **Visca over udp** to **Onvif** command converter which is implemented as server

## Converter specifics
Converter developed to handle **Vmix** software functionality. In fact, *Vmix* do not allows to work with *Onvif* cameras
but works perfectly with lots of other control protocols. Main idea was to create the mediator between *Vmix* software and
*Onvif* cameras. In practice, this is a udp socket server which emulates *Visca over udp* camera and translate received
commands into *Onvif* protocol commands.

Now available pan, tilt and zoom movements and go to home position. 
Additionally, *Vmix* allows to create camera preset and remember it's position as *Visca* camera coordinates.
Usually, *Onvif* cameras can not response it's coordinates, so this feature is implemented through *Onvif* preset
setting logic.

# Usage
Converter can be configured by either *file config* or *google sheets* document. By default