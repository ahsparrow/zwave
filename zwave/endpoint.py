import logging

from . import command

class Endpoint:
    def __init__(self, node, endpoint=1, name=""):
        self.node = node
        self.endpoint = endpoint
        self.name = name

        node.register_endpoint(self)

        self.value = 0

    def send_command(self, cmd):
        self.node.send_endpoint_command(self, cmd)

    def response(self, cmd):
        if isinstance(cmd, command.BasicReport):
            self.value = cmd.value

    def set(self, value):
        self.send_command(command.BasicSet(value))

    def get(self):
        self.send_command(command.BasicGet())

class BinarySwitch(Endpoint):
    def get(self):
        self.send_command(command.BinarySwitchGet())

    def set(self, value):
        self.send_command(command.BinarySwitchSet(value))

    def response(self, cmd):
        if isinstance(cmd, command.BinarySwitchReport):
            self.value = cmd.value
        else:
            super().response(cmd)
