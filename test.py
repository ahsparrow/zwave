import logging
logging.basicConfig(level=logging.DEBUG)

import gevent
from gevent import monkey; monkey.patch_all()

import zwave

controller = zwave.Controller()

node = zwave.Node(4, controller)
#switch = zwave.BinarySwitch(node)
#switch2 = zwave.BinarySwitch(node, 2)
switch = zwave.Endpoint(node)

controller.open("/dev/ttyACM0")
controller.start()

#gevent.spawn_later(1, node.get_config, 20)
gevent.spawn_later(1, switch.get)
gevent.spawn_later(2, switch.set, 0)
#gevent.spawn_later(4, switch.set, 0)

try:
    gevent.wait()
except KeyboardInterrupt:
    pass
