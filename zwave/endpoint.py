import logging

from . import command

class Endpoint:
    def __init__(self, node, id=1):
        self.node = node
        self.id = id

        node.register_endpoint(self)

    def send_command(self, command):
        self.node.send_endpoint_command(self, command)

    def response(self, command):
        pass

    def set(self, value):
        self.send_command(command.BasicSet(value))

    def get(self):
        self.send_command(command.BasicGet())

class BinarySwitch(Endpoint):
    def get(self):
        self.send_command(command.BinarySwitchGet())

    def set(self, value):
        self.send_command(command.BinarySwitchSet(value))
