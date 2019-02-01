import gevent
from gevent import monkey; monkey.patch_all()

import logging
logging.basicConfig(level=logging.DEBUG)

import yaml

import zwave

controller = zwave.Controller()

#config = yaml.load(open("fgs_223.yaml"))
#node = zwave.Node(controller, 4, config=config)
#switch1 = zwave.BinarySwitch(node, endpoint=1)
#switch2 = zwave.BinarySwitch(node, endpoint=2)

config = yaml.load(open("fgd_212.yaml"))
node = zwave.Node(controller, 6, name="Dimmer", config=config)
dimmer = zwave.MultilevelSwitch(node, endpoint=1)

controller.open("/dev/ttyACM0")
controller.start()

g = []
#g.append(gevent.spawn_later(1, node.set_multi_channel_association, 1, [], [[1, 1]]))
#g.append(gevent.spawn_later(4, node.get_multi_channel_association, 1))
#g.append(gevent.spawn_later(1, controller.get_init_data))
#g.append(gevent.spawn_later(1, switch1.set, 0))
#gevent.spawn_later(1, node.set_configuration, 58, 3599, "H")
#gevent.spawn_later(1, node.set_configuration, 'switch_type', 1)
#gevent.spawn_later(2, node.get_configuration, 'switch_type')
#gevent.spawn_later(1, node.set_configuration, 58, 0, "B")

#g.append(gevent.spawn_later(1, dimmer.get))
#g.append(gevent.spawn_later(1, dimmer.set, 99))
#g.append(gevent.spawn_later(3, dimmer.set, 1))
#gevent.spawn_later(1, node.set_configuration, 'minimum_brightness', 16)
gevent.spawn_later(2, node.get_configuration, 'minimum_brightness')
#gevent.spawn_later(1, node.set_configuration, 'active_power_reports', 0)
#gevent.spawn_later(2, node.get_configuration, 'active_power_reports')

try:
    gevent.joinall(g)
    gevent.wait(timeout=1000)
except KeyboardInterrupt:
    pass

