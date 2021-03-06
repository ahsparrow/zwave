from gevent import Timeout
from gevent.event import AsyncResult
import logging

from . import command

TIMEOUT = 2.0

class Endpoint:
    def __init__(self, node, endpoint=1, name=""):
        self.node = node
        self.endpoint = endpoint
        self.name = name

        node.register_endpoint(self)

        self.async_value = AsyncResult()

    def send_command(self, cmd):
        return self.node.send_endpoint_command(self, cmd)

    def response(self, cmd):
        if isinstance(cmd, command.BasicReport):
            self.value = cmd.value

    def set(self, value):
        return self.send_command(command.BasicSet(value))

    def get(self):
        return self.send_command(command.BasicGet())

class BinarySwitch(Endpoint):
    def get(self):
        self.async_value = AsyncResult()
        self.send_command(command.BinarySwitchGet())

        try:
            result = self.async_value.get(timeout=TIMEOUT)
        except Timeout:
            logging.error("BasicSwitch get timeout: %s" % self.name)
            result = None

        return result

    def set(self, value):
        return self.send_command(command.BinarySwitchSet(value))

    def response(self, cmd):
        if isinstance(cmd, command.BinarySwitchReport):
            print("response")
            self.async_value.set(cmd.value)
        else:
            super().response(cmd)

class MultilevelSwitch(Endpoint):
    def get(self):
        self.async_value = AsyncResult()
        self.send_command(command.MultilevelSwitchGet())

        try:
            result = self.async_value.get(timeout=TIMEOUT)
        except Timeout:
            logging.error("MultilevelSwitch get timeout: %s" % self.name)
            result = None

        return result

    def set(self, value):
        return self.send_command(command.MultilevelSwitchSet(value))

    def response(self, cmd):
        if isinstance(cmd, command.MultilevelSwitchReport):
            self.async_value.set(cmd.value)
        else:
            super().response(cmd)
