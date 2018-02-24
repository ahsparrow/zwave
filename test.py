import logging
logging.basicConfig(level=logging.DEBUG)

import gevent
from gevent import monkey; monkey.patch_all()

import zwave

controller = zwave.Controller("/dev/ttyACM0")
switch = zwave.Node(4, controller)

controller.open()

"""
gevent.spawn_later(1, controller.send_msg(raw_msg(zwave.API_ZW_GET_VERSION, [0xff])))

gevent.spawn_later(1, controller.send_command, 2,
                   zwave.COMMAND_CLASS_SWITCH_BINARY, zwave.SWITCH_BINARY_SET,
                   [0x00])
gevent.spawn_later(1, controller.send_command, 2,
                   zwave.COMMAND_CLASS_SWITCH_BINARY, zwave.SWITCH_BINARY_GET,
                   [])
gevent.spawn_later(1, controller.send_command, 2,
                   zwave.COMMAND_CLASS_SWITCH_BINARY, zwave.SWITCH_BINARY_GET,
                   [])
gevent.spawn_later(1, controller.send_command, 2,
                   zwave.COMMAND_CLASS_CONFIGURATION, zwave.CONFIGURATION_SET,
                   [53, 2, 0, 0x64])
gevent.spawn_later(2, controller.send_command, 2,
                   zwave.COMMAND_CLASS_CONFIGURATION, zwave.CONFIGURATION_GET,
                   [53])

gevent.spawn_later(1, switch.set, 0xff)

gevent.spawn_later(1, switch.get_association, 1)
gevent.spawn_later(4, switch.remove_association, 1, [1])
gevent.spawn_later(7, switch.get_association, 1)
"""

#gevent.spawn_later(1, switch.set_multi_channel_association, 1, [], [1, 1])
#gevent.spawn_later(1, switch.remove_multi_channel_association, 1, [], [])

#gevent.spawn_later(4, switch.get_multi_channel_association, 1)

gevent.spawn_later(1, switch.set, 0xff)
gevent.spawn_later(3, switch.set, 0x00)

gevent.spawn(controller.receive)
gevent.spawn(controller.transmit)

gevent.wait()
