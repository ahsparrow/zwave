import logging
logging.basicConfig(level=logging.DEBUG)

import gevent
from gevent import monkey; monkey.patch_all()

import zwave

controller = zwave.Controller("/dev/ttyACM0")

node = zwave.MultiChannelNode(4, controller)
switch1 = zwave.Endpoint(node, id=1)
switch2 = zwave.Endpoint(node, id=2)

controller.open()
controller.start()

gevent.spawn_later(1, switch1.get)
gevent.spawn_later(3, switch2.get)
gevent.wait()
