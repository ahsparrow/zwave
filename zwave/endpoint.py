import logging

from . import zwave

class Endpoint:
    def __init__(self, node, id=1):
        self.node = node
        self.id = id

        node.register_endpoint(self)

    def send_command(self, command):
        self.node.send_endpoint_command(self, command)

    def response(self, data):
        logging.debug("Response: " + zwave.msg_str(data))

    def set(self, value):
        self.send_command(zwave.BasicSet(value))

    def get(self):
        self.send_command(zwave.BasicGet())

class BinarySwitch(Endpoint):
    def get(self):
        self.send_command(zwave.BinarySwitchGet())

    def set(self, value):
        self.send_command(zwave.BinarySwitchSet(value))

    def response(self, data):
        logging.debug("Response: " + zwave.msg_str(data))
