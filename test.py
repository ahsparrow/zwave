import logging
logging.basicConfig(level=logging.DEBUG)

import gevent
from gevent import monkey; monkey.patch_all()

import zwave

controller = zwave.Controller()

node = zwave.Node(4, controller, open("fgs_223.yaml"))
#switch = zwave.Endpoint(node)
switch1 = zwave.Endpoint(node, id=1)
switch2 = zwave.Endpoint(node, id=2)

controller.open("/dev/ttyACM0")
controller.start()

gevent.spawn_later(1, switch1.set, 0)
gevent.spawn_later(1, switch2.set, 0xff)
gevent.spawn_later(2, switch1.set, 0xff)
gevent.spawn_later(2, switch2.set, 0)
gevent.spawn_later(3, switch1.set, 0)
gevent.spawn_later(3, switch2.set, 0xff)
gevent.spawn_later(4, switch1.set, 0xff)
gevent.spawn_later(4, switch2.set, 0)
gevent.spawn_later(5, switch1.set, 0)
#gevent.spawn_later(1, node.set_configuration, 58, 3599, "H")
#gevent.spawn_later(1, node.set_configuration, 'switch_type', 1)
#gevent.spawn_later(2, node.get_configuration, 'switch_type')

#gevent.spawn_later(1, node.set_configuration, 58, 0, "B")

try:
    gevent.wait()
except KeyboardInterrupt:
    pass

